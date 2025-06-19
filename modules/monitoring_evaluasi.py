import streamlit as st
import pandas as pd
import openai
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from calendar import month_name
import io


openai.api_key = os.getenv("OPENAI_API_KEY")

def get_sheet_map(xls: pd.ExcelFile) -> dict:
    """
    Mengembalikan dictionary nama sheet dengan key lowercase untuk lookup aman.
    """
    return {sheet.lower(): sheet for sheet in xls.sheet_names}
def upload_semua_file_monitoring(uploaded_files):
    if not uploaded_files:
        return

    for file in uploaded_files:
        try:
            xls = pd.ExcelFile(file)
            sheet_map = {sheet.lower(): sheet for sheet in xls.sheet_names}

            def load_sheet(sheet_name_expected: str, session_key: str):
                for sheet_actual in xls.sheet_names:
                    if sheet_actual.strip().lower() == sheet_name_expected.strip().lower():
                        df = xls.parse(sheet_actual)
                        st.session_state[session_key] = df
                        break

            # Load semua sheet penting ke session state
            load_sheet("program mitigasi", "copy_update_program_mitigasi")
            load_sheet("kri", "copy_update_kri")
            load_sheet("Summary RBB", "copy_summary_rbb")
            load_sheet("risiko gabungan", "copy_risiko_update_terpilih")
            load_sheet("update_risk_details", "copy_update_risk_details")
            load_sheet("deskripsi_risiko", "copy_deskripsi_risiko")
            load_sheet("key_risk_indicator", "copy_key_risk_indicator")
            load_sheet("anggaran pic", "copy_tabel_anggaran_pic")
            load_sheet("deskripsi mitigasi", "copy_deskripsi_mitigasi")
            load_sheet("residual_dampak", "copy_tabel_residual_dampak")
            load_sheet("residual_prob", "copy_tabel_residual_probabilitas")
            load_sheet("residual_eksposur", "copy_tabel_residual_eksposur")
            load_sheet("ambang batas risiko", "copy_ambang_batas_risiko")
            load_sheet("rasio keuangan", "copy_rasio_keuangan")

            # Proses informasi perusahaan
            if "informasi_perusahaan" in sheet_map:
                df = xls.parse(sheet_map["informasi_perusahaan"])
                if "Data yang dibutuhkan" in df.columns and "Input Pengguna" in df.columns:
                    st.session_state["copy_informasi_perusahaan"] = df

            # Buat salinan deskripsi risiko jika belum ada
            if "copy_tabel_risiko_gabungan" not in st.session_state:
                if "copy_deskripsi_risiko" in st.session_state:
                    st.session_state["copy_tabel_risiko_gabungan"] = st.session_state["copy_deskripsi_risiko"].copy()

            # 💡 Tambahkan: Gabungkan "Nomor Risiko" ke KRI jika tersedia
            if "copy_key_risk_indicator" in st.session_state and "copy_update_risk_details" in st.session_state:
                df_kri = st.session_state["copy_key_risk_indicator"]
                df_update = st.session_state["copy_update_risk_details"]

                if "Kode Risiko" in df_kri.columns and "Kode Risiko" in df_update.columns and "No" in df_update.columns:
                    df_nomor = df_update[["Kode Risiko", "No"]].rename(columns={"No": "Nomor Risiko"})
                    df_kri = pd.merge(df_kri, df_nomor, on="Kode Risiko", how="left")
                    st.session_state["copy_key_risk_indicator"] = df_kri

        except Exception as e:
            st.error(f"❌ Gagal membaca file: {file.name}")
            st.warning(f"Detail: {e}")



            
# ------------------- Fungsi Update -------------------
def update_program_mitigasi(edited_df):
    st.session_state["copy_program_mitigasi_lengkap"] = edited_df
    st.session_state["copy_update_program_mitigasi"] = edited_df[
        ["Kode Risiko", "Peristiwa Risiko", "Jenis Program Dalam RKAP", "PIC", "Progress Program Mitigasi (%)", "Pengelolaan Mitigasi"]

    ]
    st.session_state["update_program_mitigasi"] = True


def update_kri(edited_df):
    st.session_state["copy_update_kri"] = edited_df
    st.session_state["update_kri"] = True

def copy_summary_rbb(edited_df):
    st.session_state["copy_summary_rbb"] = edited_df
    st.session_state["update_summary_rbb"] = True



# ------------------- UI: Update Program Mitigasi -------------------
def tampilkan_update_program_mitigasi():
    st.subheader("🛠️ Update Program Mitigasi")

    df_update = st.session_state.get("copy_update_program_mitigasi", pd.DataFrame())
    df_sumber = df_update.copy()

    if df_sumber.empty:
        df_pic = st.session_state.get("copy_tabel_anggaran_pic", pd.DataFrame())
        if df_pic.empty:
            st.warning("⚠️ Tidak ada data anggaran PIC atau program mitigasi yang tersedia.")
            return

        kolom_alias = {
            "kode risiko": "Kode Risiko",
            "peristiwa risiko": "Peristiwa Risiko",
            "peristiwa": "Peristiwa Risiko",
            "jenis program dalam rkap": "Jenis Program Dalam RKAP",
            "pic": "PIC",
        }

        df_pic.columns = [kolom_alias.get(col.strip().lower(), col) for col in df_pic.columns]

        kolom_dipilih = ["Kode Risiko", "Peristiwa Risiko", "Jenis Program Dalam RKAP", "PIC"]
        if not all(k in df_pic.columns for k in kolom_dipilih):
            st.error("❌ Kolom wajib tidak ditemukan dalam tabel sumber.")
            st.write("Kolom yang tersedia:", df_pic.columns.tolist())
            return

        df_sumber = df_pic[kolom_dipilih].copy()
        df_sumber["Progress Program Mitigasi (%)"] = 0
        df_sumber["Pengelolaan Mitigasi"] = "Kurang"

    else:
        if "Progress Program Mitigasi (%)" not in df_sumber.columns:
            df_sumber["Progress Program Mitigasi (%)"] = 0

        if "Pengelolaan Mitigasi" not in df_sumber.columns:
            df_sumber["Pengelolaan Mitigasi"] = "Kurang"
        else:
            df_sumber["Pengelolaan Mitigasi"] = df_sumber["Pengelolaan Mitigasi"].replace("", "Kurang").fillna("Kurang")

        if "Keterangan" in df_sumber.columns:
            df_sumber.drop(columns=["Keterangan"], inplace=True)

    edited_df = st.data_editor(
        df_sumber,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Pengelolaan Mitigasi": st.column_config.SelectboxColumn(
                label="Pengelolaan Mitigasi",
                options=["Cukup", "Kurang"],
                required=False
            )
        },
        key="editor_program_mitigasi"
    )

    if st.button("✅ Simpan Update Program Mitigasi"):
        update_program_mitigasi(edited_df)
        st.success("✅ Update Program Mitigasi disimpan.")


def tampilkan_update_kri():
    st.subheader("📈 Update Key Risk Indicator (KRI)")

    df_update = st.session_state.get("copy_update_kri", pd.DataFrame())
    df_sumber = df_update.copy()

    if df_sumber.empty:
        df_kri = st.session_state.get("copy_key_risk_indicator", pd.DataFrame())
        if df_kri.empty:
            st.warning("⚠️ Tabel Key Risk Indicator belum tersedia di session state.")
            return

        # Normalisasi nama kolom
        kolom_alias = {
            "kode risiko": "Kode Risiko",
            "peristiwa risiko": "Peristiwa Risiko",
            "key risk indicators (kri)": "Key Risk Indicators (KRI)",
            "unit kri": "Unit KRI",
            "kri aman": "KRI Aman",
            "kri hati-hati": "KRI Hati-Hati",
            "kri bahaya": "KRI Bahaya"
        }
        df_kri.columns = [kolom_alias.get(col.strip().lower(), col) for col in df_kri.columns]

        kolom_dipilih = [
            "Kode Risiko", "Peristiwa Risiko", 
            "Key Risk Indicators (KRI)", "Unit KRI", 
            "KRI Aman", "KRI Hati-Hati", "KRI Bahaya"
        ]
        if not all(k in df_kri.columns for k in kolom_dipilih):
            st.error("❌ Kolom penting tidak ditemukan dalam tabel KRI.")
            st.write("Kolom yang tersedia:", df_kri.columns.tolist())
            return

        df_sumber = df_kri[kolom_dipilih].copy()

        # 🔍 Tambahkan "Nomor Risiko" jika tersedia dari update_risk_details
        df_risk = st.session_state.get("copy_update_risk_details", pd.DataFrame())
        if not df_risk.empty and "Kode Risiko" in df_risk.columns and "No" in df_risk.columns:
            df_nomor = df_risk[["Kode Risiko", "No"]].rename(columns={"No": "Nomor Risiko"}).drop_duplicates()
            df_sumber = pd.merge(df_sumber, df_nomor, on="Kode Risiko", how="left")

        df_sumber["KRI Saat Ini"] = ""
        df_sumber["Pengelolaan KRI"] = "Kurang"

    else:
        if "KRI Saat Ini" not in df_sumber.columns:
            df_sumber["KRI Saat Ini"] = ""
        if "Pengelolaan KRI" not in df_sumber.columns:
            df_sumber["Pengelolaan KRI"] = "Kurang"
        else:
            df_sumber["Pengelolaan KRI"] = df_sumber["Pengelolaan KRI"].replace("", "Kurang").fillna("Kurang")

    # Urutkan agar 'Nomor Risiko' muncul di awal jika ada
    if "Nomor Risiko" in df_sumber.columns:
        kolom_urut = ["Nomor Risiko"] + [col for col in df_sumber.columns if col != "Nomor Risiko"]
        df_sumber = df_sumber[kolom_urut]

    # Tampilkan editor data
    edited_df = st.data_editor(
        df_sumber,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Pengelolaan KRI": st.column_config.SelectboxColumn(
                label="Pengelolaan KRI",
                options=["Cukup", "Kurang"],
                required=False
            )
        },
        key="editor_kri"
    )

    if st.button("✅ Simpan Update KRI"):
        update_kri(edited_df)
        st.success("✅ Update KRI disimpan.")

# ------------------- UI: Ringkasan RBB + Pencapaian -------------------
def tampilkan_summary_rbb_dengan_pencapaian():
    st.subheader("📋Update Risk-Based Budgeting")

    df_summary = st.session_state.get("copy_summary_rbb", pd.DataFrame())
    if isinstance(df_summary, pd.DataFrame) and not df_summary.empty:
        if "Pencapaian Saat Ini" not in df_summary.columns:
            df_summary["Pencapaian Saat Ini"] = ""

        edited_df = st.data_editor(
            df_summary,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_summary_rbb"
        )

        if st.button("✅ Simpan Update RBB"):
            copy_summary_rbb(edited_df)
            st.success("✅ Update RBB disimpan.")
    else:
        st.warning("⚠️ Tabel Ringkasan RBB belum tersedia di session state.")
        
def gabungkan_tabel_update_risiko():

    df_mitigasi = st.session_state.get("copy_update_program_mitigasi", pd.DataFrame())
    df_kri = st.session_state.get("copy_update_kri", pd.DataFrame())

    if df_mitigasi.empty or df_kri.empty:
        st.warning("⚠️ Data update Program Mitigasi atau KRI belum tersedia.")
        return

    # Gabungkan berdasarkan 'Kode Risiko'
    df_gabungan = pd.merge(
        df_mitigasi,
        df_kri,
        on="Kode Risiko",
        how="outer",
        suffixes=("_Mitigasi", "_KRI")
    )


    # Simpan ke session_state jika perlu digunakan kembali
    st.session_state["copy_gabungan_update_risiko"] = df_gabungan

def evaluasi_kinerja_rbb():
 
    df_rbb = st.session_state.get("copy_summary_rbb", pd.DataFrame())
    if df_rbb.empty:
        st.warning("⚠️ Data Ringkasan RBB belum tersedia.")
        return

    kolom_diperlukan = ["Kategori", "Nilai", "Pencapaian Saat Ini"]
    if not all(k in df_rbb.columns for k in kolom_diperlukan):
        st.error("❌ Kolom yang diperlukan tidak ditemukan.")
        return

    df_rbb["Nilai"] = pd.to_numeric(df_rbb["Nilai"], errors="coerce")
    df_rbb["Pencapaian Saat Ini"] = pd.to_numeric(df_rbb["Pencapaian Saat Ini"], errors="coerce")

    bulan_ke = datetime.now().month

    for idx, row in df_rbb.iterrows():
        target = row["Nilai"]
        pencapaian = row["Pencapaian Saat Ini"]

        if pd.isna(target) or pd.isna(pencapaian):
            evaluasi = "❓ Data Tidak Lengkap"
            pengelolaan = "Kurang"
            persentase = 0
        else:
            target_berjalan = (bulan_ke / 12) * target
            # Hitung persentase capaian dengan arah
            persentase = (pencapaian / target) * 100 if target != 0 else 0

            if target >= 0:
                tercapai = pencapaian >= target_berjalan
            else:
                tercapai = pencapaian <= target_berjalan  # biaya/kerugian lebih kecil lebih baik

            evaluasi = f"✅ Sesuai Bulan ke-{bulan_ke}" if tercapai else f"⚠️ Di Bawah Bulan ke-{bulan_ke}"
            pengelolaan = "Cukup" if tercapai else "Kurang"

        df_rbb.at[idx, "Persentase Capaian (%)"] = round(persentase, 1)
        df_rbb.at[idx, "Evaluasi"] = evaluasi
        df_rbb.at[idx, "Pengelolaan Kinerja"] = pengelolaan


    st.session_state["copy_summary_rbb"] = df_rbb
    


def tampilkan_residual_eksposur():

    # Ambil dari session_state
    df_prob = st.session_state.get("copy_tabel_residual_probabilitas", pd.DataFrame())
    df_dampak = st.session_state.get("copy_tabel_residual_dampak", pd.DataFrame())
    df_eksposur = st.session_state.get("copy_tabel_residual_eksposur", pd.DataFrame())

    # Validasi awal
    if df_prob.empty and df_dampak.empty and df_eksposur.empty:
        st.warning("⚠️ Semua sheet residual (probabilitas, dampak, eksposur) belum tersedia.")
        return

    # Normalisasi kolom kunci
    for df in [df_prob, df_dampak, df_eksposur]:
        if not df.empty:
            df.columns = df.columns.str.strip()
            if "kode risiko" in df.columns.str.lower():
                df.rename(columns={col: "Kode Risiko" for col in df.columns if col.strip().lower() == "kode risiko"}, inplace=True)

    # Gabungkan berdasarkan "Kode Risiko"
    df_gabungan = df_prob.copy()
    if not df_dampak.empty:
        df_gabungan = pd.merge(df_gabungan, df_dampak, on="Kode Risiko", how="outer", suffixes=("", "_dampak"))
    if not df_eksposur.empty:
        df_gabungan = pd.merge(df_gabungan, df_eksposur, on="Kode Risiko", how="outer", suffixes=("", "_eksposur"))

    # Hapus kolom duplikat berdasarkan nama
    df_gabungan = df_gabungan.loc[:, ~df_gabungan.columns.duplicated()]


    # Simpan ke session_state jika diperlukan
    st.session_state["copy_tabel_residual_gabungan"] = df_gabungan

def tampilkan_indikator_pengelolaan():

    # --- 1. Pengelolaan KRI ---
    df_kri = st.session_state.get("copy_update_kri", pd.DataFrame())
    kri_summary = {"Cukup": 0, "Kurang": 0}
    if not df_kri.empty and "Pengelolaan KRI" in df_kri.columns:
        kri_summary = df_kri["Pengelolaan KRI"].fillna("Kurang").value_counts().reindex(["Cukup", "Kurang"], fill_value=0).to_dict()

    # --- 2. Pengelolaan Mitigasi ---
    df_mitigasi = st.session_state.get("copy_update_program_mitigasi", pd.DataFrame())
    mitigasi_summary = {"Cukup": 0, "Kurang": 0}
    if not df_mitigasi.empty and "Pengelolaan Mitigasi" in df_mitigasi.columns:
        mitigasi_summary = df_mitigasi["Pengelolaan Mitigasi"].fillna("Kurang").value_counts().reindex(["Cukup", "Kurang"], fill_value=0).to_dict()

    # --- 3. Pengelolaan Kinerja RBB ---
    df_rbb = st.session_state.get("copy_summary_rbb", pd.DataFrame())
    kinerja_summary = {"Cukup": 0, "Kurang": 0}
    if not df_rbb.empty and "Pengelolaan Kinerja" in df_rbb.columns:
        kinerja_summary = df_rbb["Pengelolaan Kinerja"].fillna("Kurang").value_counts().reindex(["Cukup", "Kurang"], fill_value=0).to_dict()

    # --- Tampilkan Ringkasan ---
    indikator_df = pd.DataFrame({
        "Aspek": ["Pengelolaan KRI", "Pengelolaan Mitigasi", "Pengelolaan Kinerja"],
        "Cukup": [kri_summary["Cukup"], mitigasi_summary["Cukup"], kinerja_summary["Cukup"]],
        "Kurang": [kri_summary["Kurang"], mitigasi_summary["Kurang"], kinerja_summary["Kurang"]]
    })


    # Simpan jika diperlukan untuk ekspor atau visualisasi
    st.session_state["indikator_pengelolaan_summary"] = indikator_df

def hitung_score_pengelolaan_risiko():
    st.subheader("📈 Skor Pengelolaan Risiko Berdasarkan Indikator")

    # 1. Pengelolaan KRI
    df_kri = st.session_state.get("copy_update_kri", pd.DataFrame())
    if not df_kri.empty and "Pengelolaan KRI" in df_kri.columns:
        total_kri = len(df_kri)
        cukup_kri = (df_kri["Pengelolaan KRI"] == "Cukup").sum()
        skor_kri = (cukup_kri / total_kri) * 100 if total_kri > 0 else 0
    else:
        skor_kri = 0

    # 2. Pengelolaan Mitigasi
    df_mitigasi = st.session_state.get("copy_update_program_mitigasi", pd.DataFrame())
    if not df_mitigasi.empty and "Pengelolaan Mitigasi" in df_mitigasi.columns:
        total_mitigasi = len(df_mitigasi)
        cukup_mitigasi = (df_mitigasi["Pengelolaan Mitigasi"] == "Cukup").sum()
        skor_mitigasi = (cukup_mitigasi / total_mitigasi) * 100 if total_mitigasi > 0 else 0
    else:
        skor_mitigasi = 0

    # 3. Pengelolaan Kinerja
    df_rbb = st.session_state.get("copy_summary_rbb", pd.DataFrame())
    if not df_rbb.empty and "Pengelolaan Kinerja" in df_rbb.columns:
        total_rbb = len(df_rbb)
        cukup_rbb = (df_rbb["Pengelolaan Kinerja"] == "Cukup").sum()
        skor_rbb = (cukup_rbb / total_rbb) * 100 if total_rbb > 0 else 0
    else:
        skor_rbb = 0

    # Hitung skor total berbobot (Bobot terbaru: 20% + 20% + 60%)
    skor_total = (skor_kri * 0.20) + (skor_mitigasi * 0.20) + (skor_rbb * 0.60)

    # Tampilkan hasil
    st.markdown(f"""
    **📊 Rincian Skor:**
    - Pengelolaan KRI: {skor_kri:.1f}% × 20% = {skor_kri * 0.20:.1f}
    - Pengelolaan Mitigasi: {skor_mitigasi:.1f}% × 20% = {skor_mitigasi * 0.20:.1f}
    - Pengelolaan Kinerja: {skor_rbb:.1f}% × 60% = {skor_rbb * 0.60:.1f}
    """)
    st.success(f"🎯 **Skor Pengelolaan Risiko Total: {skor_total:.1f} / 100**")

    # Simpan ke session_state
    st.session_state["skor_pengelolaan_risiko"] = skor_total

def update_matriks_risiko():
    st.subheader("🧮 Update Matriks Risiko Residual per Kuartal")

    df = st.session_state.get("copy_tabel_residual_gabungan", pd.DataFrame())
    if df.empty:
        st.warning("⚠️ Tabel Residual Gabungan belum tersedia.")
        return

    # Tentukan kuartal saat ini
    bulan = datetime.now().month
    if bulan <= 3:
        q = "Q1"
    elif bulan <= 6:
        q = "Q2"
    elif bulan <= 9:
        q = "Q3"
    else:
        q = "Q4"

    st.info(f"📆 Kuartal saat ini: **{q}**")

    skor_pengelolaan_risiko = 62.5  # dalam persen

    # Ambil kolom dinamis
    kol_skala_prob = f"Skala {q}"
    kol_skala_dampak = f"Skala {q}_dampak"
    kol_eksposur = f"Nilai {q}_eksposur"

    kol_diperlukan = [kol_skala_prob, kol_skala_dampak, kol_eksposur]
    if not all(k in df.columns for k in kol_diperlukan):
        st.error("❌ Kolom data kuartal tidak lengkap.")
        st.write("Kolom yang tersedia:", df.columns.tolist())
        return

    # Hitung Probabilitas dan Dampak Saat Ini, dibulatkan ke atas
    df["Probabilitas Saat Ini"] = np.ceil(((100 - skor_pengelolaan_risiko)/100) + df[kol_skala_prob])
    df["Skala Dampak Saat Ini"] = np.ceil(((100 - skor_pengelolaan_risiko)/100) + df[kol_skala_dampak])

    # Eksposur Saat Ini
    df["Eksposur Saat Ini"] = (((100 - skor_pengelolaan_risiko)/100) * df[kol_eksposur]) + df[kol_eksposur]

    # Buat output
    df_output = df[[
        "Kode Risiko", "Peristiwa Risiko", "Kategori Risiko T2 & T3 KBUMN",
        kol_skala_prob, "Probabilitas Saat Ini",
        kol_skala_dampak, "Skala Dampak Saat Ini",
        kol_eksposur, "Eksposur Saat Ini"
    ]].copy()


    st.session_state["copy_matriks_risiko_kuartal"] = df_output

def tampilkan_heatmap_risiko_kuartal():
    st.subheader("🌡️ Heatmap Risiko Residual Kuartal Saat Ini")

    df = st.session_state.get("copy_matriks_risiko_kuartal", pd.DataFrame())
    if df.empty:
        st.warning("⚠️ Data matriks risiko kuartal belum tersedia.")
        return

    risk_labels = {
        (1, 1): ('Low', 1), (1, 2): ('Low', 5), (1, 3): ('Low to Moderate', 10), (1, 4): ('Moderate', 15), (1, 5): ('High', 20),
        (2, 1): ('Low', 2), (2, 2): ('Low to Moderate', 6), (2, 3): ('Low to Moderate', 11), (2, 4): ('Moderate to High', 16), (2, 5): ('High', 21),
        (3, 1): ('Low', 3), (3, 2): ('Low to Moderate', 8), (3, 3): ('Moderate', 13), (3, 4): ('Moderate to High', 18), (3, 5): ('High', 23),
        (4, 1): ('Low', 4), (4, 2): ('Low to Moderate', 9), (4, 3): ('Moderate', 14), (4, 4): ('Moderate to High', 19), (4, 5): ('High', 24),
        (5, 1): ('Low to Moderate', 7), (5, 2): ('Moderate', 12), (5, 3): ('Moderate to High', 17), (5, 4): ('High', 22), (5, 5): ('High', 25)
    }

    color_matrix = np.full((5, 5), 'white', dtype=object)
    risk_matrix = [['' for _ in range(5)] for _ in range(5)]

    for coord, (label, _) in risk_labels.items():
        i, j = coord[0] - 1, coord[1] - 1
        color_matrix[i][j] = {
            'High': 'red',
            'Moderate to High': 'orange',
            'Moderate': 'yellow',
            'Low to Moderate': 'lightgreen',
            'Low': 'darkgreen'
        }.get(label, 'white')

    for idx, row in df.iterrows():
        try:
            prob = int(row.get('Probabilitas Saat Ini', 0))
            damp = int(row.get('Skala Dampak Saat Ini', 0))
            kode = str(row.get('Kode Risiko', '')).strip()

            if 1 <= prob <= 5 and 1 <= damp <= 5:
                i, j = prob - 1, damp - 1
                existing = risk_matrix[i][j].replace("\n", ", ").split(", ") if risk_matrix[i][j] else []
                if kode and kode not in existing:
                    existing.append(kode)
                lines = [", ".join(existing[k:k+4]) for k in range(0, len(existing), 4)]
                risk_matrix[i][j] = "\n".join(lines)
        except:
            continue

    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    for i in range(5):
        for j in range(5):
            ax.add_patch(plt.Rectangle((j, i), 1, 1, color=color_matrix[i][j], edgecolor='black'))
            label, number = risk_labels.get((i + 1, j + 1), ('', ''))
            ax.text(j + 0.5, i + 0.7, label, ha='center', va='center', fontsize=5)
            ax.text(j + 0.5, i + 0.5, str(number), ha='center', va='center', fontsize=5)
            ax.text(j + 0.5, i + 0.3, risk_matrix[i][j], ha='center', va='center', fontsize=8, color='blue')

    ax.set_xlim(0, 5)
    ax.set_ylim(0, 5)
    ax.set_xticks(np.arange(5) + 0.5)
    ax.set_yticks(np.arange(5) + 0.5)
    ax.set_xticklabels([1, 2, 3, 4, 5], fontsize=7)
    ax.set_yticklabels([1, 2, 3, 4, 5], fontsize=7)
    ax.set_xlabel("Skala Dampak")
    ax.set_ylabel("Skala Probabilitas")
    ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)
    plt.tight_layout()
    st.pyplot(fig)
    
def gabungkan_semua_data_monitoring():
    st.subheader("🧾 Gabungan Semua Data Monitoring")

    df_gabungan = st.session_state.get("copy_gabungan_update_risiko", pd.DataFrame())
    df_perusahaan = st.session_state.get("copy_informasi_perusahaan", pd.DataFrame())
    df_matriks = st.session_state.get("copy_matriks_risiko_kuartal", pd.DataFrame())

    # Validasi
    if df_gabungan.empty:
        st.warning("⚠️ Gabungan Program Mitigasi dan KRI belum tersedia.")
        return
    if df_matriks.empty:
        st.warning("⚠️ Matriks Risiko Residual per Kuartal belum tersedia.")
        return
    if df_perusahaan.empty:
        st.warning("⚠️ Informasi Perusahaan belum tersedia.")
        return

    # Ekstrak semua informasi perusahaan
    try:
        df_info = df_perusahaan.copy()
        df_info.columns = df_info.columns.str.strip()
        df_info = df_info.set_index("Data yang dibutuhkan")["Input Pengguna"].to_frame().T.reset_index(drop=True)
        df_info.columns = [col.strip() for col in df_info.columns]
    except:
        st.error("❌ Gagal memproses informasi perusahaan.")
        return

    # Tambahkan kolom perusahaan ke df_gabungan dan df_matriks
    for col in df_info.columns:
        df_gabungan[col] = df_info.at[0, col]
        df_matriks[col] = df_info.at[0, col]

    # Gabungkan berdasarkan 'Kode Risiko'
    df_final = pd.merge(
        df_gabungan,
        df_matriks,
        on=["Kode Risiko"] + df_info.columns.tolist(),
        how="outer"
    )

    # 💡 Tambahkan Nomor Risiko dari update_risk_details
    df_update = st.session_state.get("copy_update_risk_details", pd.DataFrame())
    if not df_update.empty and "Kode Risiko" in df_update.columns and "No" in df_update.columns:
        df_nomor = df_update[["Kode Risiko", "No"]].rename(columns={"No": "Nomor Risiko"})
        df_final = pd.merge(df_final, df_nomor, on="Kode Risiko", how="left")

    # Hapus kolom duplikat
    df_final = df_final.loc[:, ~df_final.columns.duplicated()]

    # Urutkan kolom: info perusahaan → Nomor Risiko → sisanya
    kolom_perusahaan = df_info.columns.tolist()
    kolom_awal = kolom_perusahaan + (["Nomor Risiko"] if "Nomor Risiko" in df_final.columns else [])
    kolom_lain = [k for k in df_final.columns if k not in kolom_awal]
    df_final = df_final[kolom_awal + kolom_lain]

    # Simpan dan tampilkan
    st.session_state["copy_semua_data_monitoring"] = df_final
    st.dataframe(df_final, use_container_width=True)

def unduh_data_monitoring_gabungan():
    st.subheader("⬇️ Unduh Data Gabungan Monitoring")

    df_final = st.session_state.get("copy_semua_data_monitoring", pd.DataFrame())
    if df_final.empty:
        st.warning("⚠️ Data gabungan belum tersedia.")
        return

    # Ambil kode perusahaan dari kolom jika ada
    kode_perusahaan = "PERUSAHAAN"
    for col in df_final.columns:
        if col.lower() in ["kode perusahaan", "kode_perusahaan"]:
            kode_perusahaan = str(df_final[col].iloc[0]).strip().replace(" ", "_").upper()
            break

    # Ambil tanggal saat ini
    bulan = datetime.now().strftime("%B").upper()
    tahun = datetime.now().year

    # Buat nama file
    nama_file = f"monitoring_{kode_perusahaan}_{bulan}_{tahun}.xlsx"

    # Simpan ke buffer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Monitoring')
    output.seek(0)

    st.download_button(
        label="📥 Klik untuk Unduh Excel",
        data=output,
        file_name=nama_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def main():

    st.title("📊 Monitoring dan Evaluasi Risiko")

    st.markdown("### 📤 Upload File Monitoring")
    uploaded_files = st.file_uploader(
        "Silahkan unggah 5 file: perlakuan_risiko, risk_based_budgeting, Residual_Dampak, Profil_Risiko, Profil_Perusahaan",
        type=["xlsx"],
        accept_multiple_files=True,
        key="upload_monitoring_semua"
    )

    if uploaded_files:
        upload_semua_file_monitoring(uploaded_files)

    st.markdown("---")

    with st.expander("🛠️ Update Program Mitigasi", expanded=True):
        tampilkan_update_program_mitigasi()

    with st.expander("📈 Update Key Risk Indicator (KRI)", expanded=True):
        tampilkan_update_kri()

    with st.expander("📋 Update Risk-Based Budgeting (RBB)", expanded=True):
        tampilkan_summary_rbb_dengan_pencapaian()
    
    with st.expander("📎 Gabungan Update Program Mitigasi dan KRI"):
        gabungkan_tabel_update_risiko()
    
    with st.expander("📊 Evaluasi Kinerja Laba Sebelum Pajak"):
        evaluasi_kinerja_rbb()
        
    with st.expander("📉 Residual Eksposur"):
        tampilkan_residual_eksposur()
        
    with st.expander("📊 Ringkasan Indikator Pengelolaan Risiko"):
        tampilkan_indikator_pengelolaan()
        
    with st.expander("📈 Skor Pengelolaan Risiko"):
        hitung_score_pengelolaan_risiko()
        
    with st.expander("🧮 Update Matriks Risiko Residual per Kuartal"):
        update_matriks_risiko()
    
    tampilkan_heatmap_risiko_kuartal()
    
    with st.expander("🧮 Data Monitoring All"):
        gabungkan_semua_data_monitoring()
    
    unduh_data_monitoring_gabungan()

if __name__ == "__main__":
    main()
