import streamlit as st
import pandas as pd
import openai
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from calendar import month_name


openai.api_key = os.getenv("OPENAI_API_KEY")

# ------------------- Fungsi Update -------------------
def update_program_mitigasi(edited_df):
    st.session_state["copy_program_mitigasi_lengkap"] = edited_df
    st.session_state["copy_update_program_mitigasi"] = edited_df[
        ["Kode Risiko", "Peristiwa Risiko", "Jenis Program Dalam RKAP", "PIC", "Progress Program Mitigasi (%)", "Keterangan"]
    ]
    st.session_state["update_program_mitigasi"] = True


def update_kri(edited_df):
    st.session_state["copy_update_kri"] = edited_df
    st.session_state["update_kri"] = True

def copy_summary_rbb(edited_df):
    st.session_state["copy_summary_rbb"] = edited_df
    st.session_state["update_summary_rbb"] = True

def update_residual_q1(edited_df):
    st.session_state["copy_tabel_residual_q1"] = edited_df
    st.session_state["update_residual_q1"] = True

def update_risiko_tergabung(edited_df):
    st.session_state["copy_tabel_risiko_gabungan"] = edited_df
    st.session_state["update_tabel_risiko_gabungan"] = True

# ------------------- UI: Update Program Mitigasi -------------------
def tampilkan_update_program_mitigasi():
    st.subheader("🛠️ Update Program Mitigasi (silahkan isi %)")

    df = st.session_state.get("copy_tabel_anggaran_pic")
    if isinstance(df, pd.DataFrame) and not df.empty:
        kolom_dipilih = ["Kode Risiko", "Peristiwa Risiko", "Jenis Program Dalam RKAP", "PIC"]
        df_mitigasi = df[kolom_dipilih].copy()

        # Tambahkan kolom default kosong untuk "Progress" dan "Keterangan"
        df_mitigasi["Progress Program Mitigasi (%)"] = 0
        df_mitigasi["Keterangan"] = ""

        # Overwrite jika data update sebelumnya tersedia
        df_update = st.session_state.get("copy_update_program_mitigasi", pd.DataFrame())
        if "Kode Risiko" in df_update.columns:
            df_update_indexed = df_update.set_index("Kode Risiko")

            if "Progress Program Mitigasi (%)" in df_update_indexed.columns:
                df_mitigasi["Progress Program Mitigasi (%)"] = df_mitigasi["Kode Risiko"].map(
                    df_update_indexed["Progress Program Mitigasi (%)"]
                ).fillna(0)

            if "Keterangan" in df_update_indexed.columns:
                df_mitigasi["Keterangan"] = df_mitigasi["Kode Risiko"].map(
                    df_update_indexed["Keterangan"]
                ).fillna("")

        # Tampilkan editor
        edited_df = st.data_editor(
            df_mitigasi,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_program_mitigasi"
        )

        if st.button("✅ Simpan Update Program Mitigasi"):
            update_program_mitigasi(edited_df)
            st.success("✅ Update Program Mitigasi disimpan.")
    else:
        st.warning("⚠️ Tabel anggaran PIC belum tersedia di session state.")



def tampilkan_update_kri():
    st.subheader("📈 Update Key Risk Indicator (KRI)")

    df = st.session_state.get("copy_key_risk_indicator")
    if isinstance(df, pd.DataFrame) and not df.empty:
        kolom_dipilih = [
            "Kode Risiko", "Peristiwa Risiko", 
            "Key Risk Indicators (KRI)", "Unit KRI", 
            "KRI Aman", "KRI Hati-Hati", "KRI Bahaya"
        ]

        df_kri = df[kolom_dipilih].copy()

        df_update = st.session_state.get("copy_update_kri", pd.DataFrame())
        if "Kode Risiko" in df_update.columns:
            df_update_indexed = df_update.set_index("Kode Risiko")

            df_kri["KRI Saat Ini"] = df_kri["Kode Risiko"].map(
                df_update_indexed["KRI Saat Ini"] if "KRI Saat Ini" in df_update_indexed.columns else ""
            ).fillna("")

            df_kri["Pengelolaan KRI"] = df_kri["Kode Risiko"].map(
                df_update_indexed["Pengelolaan KRI"] if "Pengelolaan KRI" in df_update_indexed.columns else ""
            ).fillna("")
        else:
            df_kri["KRI Saat Ini"] = ""
            df_kri["Pengelolaan KRI"] = ""

        edited_df = st.data_editor(
            df_kri,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Pengelolaan KRI": st.column_config.SelectboxColumn(
                    label="Pengelolaan KRI",
                    options=["Kurang", "Cukup"],
                    required=False
                )
            },
            key="editor_kri"
        )

        if st.button("✅ Simpan Update KRI"):
            update_kri(edited_df)
            st.success("✅ Update KRI disimpan.")
    else:
        st.warning("⚠️ Tabel Key Risk Indicator belum tersedia di session state.")


# ------------------- UI: Ringkasan RBB + Pencapaian -------------------
def tampilkan_summary_rbb_dengan_pencapaian():
    st.subheader("📋 Ringkasan Risk-Based Budgeting + Pencapaian")

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


def tampilkan_kinerja_keuangan():
    st.subheader("📊 % Kinerja Keuangan: Total Proyeksi Pendapatan")

    df = st.session_state.get("copy_summary_rbb")
    if isinstance(df, pd.DataFrame) and not df.empty:
        df["Nilai"] = pd.to_numeric(df["Nilai"], errors="coerce")
        df["Pencapaian Saat Ini"] = pd.to_numeric(df["Pencapaian Saat Ini"], errors="coerce")

        df_target = df[df["Kategori"] == "Total Proyeksi Pendapatan"].copy()
        if df_target.empty:
            st.warning("⚠️ Baris 'Total Proyeksi Pendapatan' tidak ditemukan.")
            return

        nilai = df_target.iloc[0]["Nilai"]
        pencapaian = df_target.iloc[0]["Pencapaian Saat Ini"]
        persentase = (pencapaian / nilai) * 100 if nilai else None

        hasil = pd.DataFrame({
            "Kategori": ["Total Proyeksi Pendapatan"],
            "Nilai": [nilai],
            "Pencapaian Saat Ini": [pencapaian],
            "% Kinerja Keuangan": [f"{persentase:.2f}%" if persentase else "-"]
        })

        st.dataframe(hasil, use_container_width=True)
    else:
        st.warning("⚠️ Data Ringkasan RBB belum tersedia di session state.")

# ------------------- UI: Residual Q1 -------------------
def tampilkan_residual_q1():
    st.subheader("🧮 Residual Risk - Q1")

    df = st.session_state.get("copy_tabel_residual_q1")
    kolom_ditampilkan = [
        "No", "Kode Risiko", "Peristiwa Risiko_Probabilitas", 
        "Skala Probabilitas Q1", "Skala Q2_Probabilitas", 
        "Skala Q3_Probabilitas", "Skala Q4_Probabilitas",
        "Skala Dampak Q1", "Skala Q2_Dampak", 
        "Skala Q3_Dampak", "Skala Q4_Dampak"
    ]

    if isinstance(df, pd.DataFrame) and not df.empty:
        missing = [kol for kol in kolom_ditampilkan if kol not in df.columns]
        if missing:
            st.error(f"❌ Kolom berikut tidak ditemukan dalam tabel residual Q1: {missing}")
        else:
            edited_df = st.data_editor(
                df[kolom_ditampilkan].copy(),
                use_container_width=True,
                num_rows="dynamic"
            )

            if st.button("✅ Simpan Update Residual Q1"):
                update_residual_q1(edited_df)
                st.success("✅ Update residual risiko Q1 disimpan.")
    else:
        st.info("ℹ️ Data residual risiko Q1 belum tersedia di session state.")
def tampilkan_gabungan_update_risiko():
    # Ambil semua data dari session state
    df_risiko = st.session_state.get("copy_tabel_risiko_gabungan", pd.DataFrame())
    df_mitigasi = st.session_state.get("copy_update_program_mitigasi", pd.DataFrame())
    df_kri = st.session_state.get("copy_update_kri", pd.DataFrame())
    df_kri_lengkap = st.session_state.get("copy_key_risk_indicator", pd.DataFrame())
    df_residual = st.session_state.get("copy_tabel_residual_q1", pd.DataFrame())
    df_summary = st.session_state.get("copy_summary_rbb", pd.DataFrame())

    if df_risiko.empty:
        st.warning("⚠️ Data risiko gabungan belum tersedia.")
        return pd.DataFrame()

    df = df_risiko.copy()

    # 🔄 MERGE DATA TAMBAHAN
    if not df_mitigasi.empty:
        kolom_mitigasi = ["Jenis Program Dalam RKAP", "PIC", "Progress Program Mitigasi (%)", "Keterangan"]
        df = df.merge(df_mitigasi[["Kode Risiko"] + kolom_mitigasi].drop_duplicates(), on="Kode Risiko", how="left")

    if not df_kri.empty:
        kolom_kri = ["Kode Risiko", "KRI Saat Ini", "Pengelolaan KRI"]
        df = df.merge(df_kri[kolom_kri].drop_duplicates(), on="Kode Risiko", how="left")

    if not df_kri_lengkap.empty:
        kolom_kri_lengkap = ["Kode Risiko", "Key Risk Indicators (KRI)", "Unit KRI", "KRI Aman", "KRI Hati-Hati", "KRI Bahaya"]
        df = df.merge(df_kri_lengkap[kolom_kri_lengkap].drop_duplicates(), on="Kode Risiko", how="left")

    if not df_residual.empty:
        kolom_residual = [
            "Kode Risiko", "Skala Probabilitas Q1", "Skala Q2_Probabilitas", "Skala Q3_Probabilitas", "Skala Q4_Probabilitas",
            "Skala Dampak Q1", "Skala Q2_Dampak", "Skala Q3_Dampak", "Skala Q4_Dampak"
        ]
        df = df.merge(df_residual[kolom_residual].drop_duplicates(), on="Kode Risiko", how="left")

    if df_summary.empty or "Kategori" not in df_summary.columns:
        st.warning("⚠️ Data summary RBB belum lengkap atau kosong.")
        return pd.DataFrame()

    # 🏢 Tambahkan informasi perusahaan jika belum ada
    df_info = st.session_state.get("copy_informasi_perusahaan", pd.DataFrame())
    info_dict = {}
    if isinstance(df_info, pd.DataFrame) and not df_info.empty:
        for _, row in df_info.iterrows():
            info_dict[row["Data yang dibutuhkan"]] = row["Input Pengguna"]

    kolom_info = [
        ("Kode Perusahaan", "Kode Perusahaan"),
        ("Nama Perusahaan", "Nama Perusahaan"),
        ("Alamat", "Alamat"),
        ("Jenis Bisnis", "Jenis Bisnis"),
        ("Direktorat", "Direktorat"),
        ("Divisi", "Divisi"),
        ("Departemen", "Departemen"),
    ]

    for idx, (kolom, kunci) in enumerate(kolom_info):
        if kolom not in df.columns:
            df.insert(idx, kolom, info_dict.get(kunci, ""))

    # 🧮 Perhitungan
    bulan_saat_ini = datetime.now().month
    kuartal = (bulan_saat_ini - 1) // 3 + 1

    df_summary["Nilai"] = pd.to_numeric(df_summary["Nilai"], errors="coerce")
    df_summary["Pencapaian Saat Ini"] = pd.to_numeric(df_summary["Pencapaian Saat Ini"], errors="coerce")

    nilai_pendapatan = df_summary.loc[df_summary["Kategori"] == "Total Proyeksi Pendapatan", "Nilai"].sum()
    pencapaian_pendapatan = df_summary.loc[df_summary["Kategori"] == "Total Proyeksi Pendapatan", "Pencapaian Saat Ini"].sum()
    nilai_biaya = df_summary.loc[df_summary["Kategori"] == "Total Biaya", "Nilai"].sum()
    pencapaian_biaya = df_summary.loc[df_summary["Kategori"] == "Total Biaya", "Pencapaian Saat Ini"].sum()

    df["Nilai Pendapatan"] = nilai_pendapatan
    df["Pencapaian Pendapatan"] = pencapaian_pendapatan
    df["Nilai Biaya"] = nilai_biaya
    df["Pencapaian Biaya"] = pencapaian_biaya

    persentase = (pencapaian_pendapatan / nilai_pendapatan) * 100 if nilai_pendapatan else None
    persentase_float = persentase if persentase is not None else 0
    df["% Kinerja Keuangan"] = f"{persentase_float:.2f}%" if persentase is not None else "-"

    df["Nilai Dampak"] = pd.to_numeric(df.get("Nilai Dampak"), errors="coerce")
    df["Dampak Residual Saat Ini"] = df["Nilai Dampak"] * ((100 - persentase_float) / 100)
    df["Dampak Residual Saat Ini"] = df["Dampak Residual Saat Ini"].apply(
        lambda x: f"{int(round(x)):,}" if pd.notnull(x) else "-"
    )

    batas_biaya_bulanan = (nilai_biaya / 12) * bulan_saat_ini if nilai_biaya else 0
    batas_pendapatan_bulanan = (nilai_pendapatan / 12) * bulan_saat_ini if nilai_pendapatan else 0

    df["Status Kinerja Biaya"] = df["Pencapaian Biaya"].apply(
        lambda x: "Kurang" if x > batas_biaya_bulanan else "Cukup"
    )
    df["Status Kinerja Pendapatan"] = df["Pencapaian Pendapatan"].apply(
        lambda x: "Kurang" if x < batas_pendapatan_bulanan else "Cukup"
    )

    target_progress = (100 / 12) * bulan_saat_ini
    df["Progress Program Mitigasi (%)"] = pd.to_numeric(df.get("Progress Program Mitigasi (%)", 0), errors="coerce").fillna(0)
    df["Pengelolaan Mitigasi"] = df["Progress Program Mitigasi (%)"].apply(
        lambda x: "Cukup" if x >= target_progress else "Kurang"
    )

    mapping_prob = {
        1: "Skala Probabilitas Q1",
        2: "Skala Q2_Probabilitas",
        3: "Skala Q3_Probabilitas",
        4: "Skala Q4_Probabilitas"
    }
    kolom_prob = mapping_prob.get(kuartal, "Skala Probabilitas Q1")
    df[kolom_prob] = pd.to_numeric(df.get(kolom_prob), errors="coerce")

    def hitung_probabilitas_saat_ini(row):
        nilai = row.get(kolom_prob)
        if pd.isna(nilai):
            return "-"
        if row.get("Pengelolaan KRI") == "Kurang" or row.get("Pengelolaan Mitigasi") == "Kurang":
            return min(nilai + 1, 5)
        return nilai

    df["Skala Probabilitas Saat Ini"] = df.apply(hitung_probabilitas_saat_ini, axis=1)

    mapping_dampak = {
        1: "Skala Dampak Q1",
        2: "Skala Q2_Dampak",
        3: "Skala Q3_Dampak",
        4: "Skala Q4_Dampak"
    }
    kolom_dampak = mapping_dampak.get(kuartal, "Skala Dampak Q1")
    df[kolom_dampak] = pd.to_numeric(df.get(kolom_dampak), errors="coerce")

    def hitung_skala_dampak_saat_ini(row):
        nilai = row.get(kolom_dampak)
        if pd.isna(nilai):
            return "-"
        if row.get("Status Kinerja Biaya") == "Kurang" or row.get("Status Kinerja Pendapatan") == "Kurang":
            return min(nilai + 1, 5)
        return nilai

    df["Skala Dampak Saat Ini"] = df.apply(hitung_skala_dampak_saat_ini, axis=1)

    df["Skala Dampak BUMN"] = df["Skala Dampak Saat Ini"]
    df["Skala Probabilitas BUMN"] = df["Skala Probabilitas Saat Ini"]
    df["Skala Risiko BUMN"] = pd.to_numeric(df["Skala Dampak BUMN"], errors="coerce") * pd.to_numeric(df["Skala Probabilitas BUMN"], errors="coerce")

    def tentukan_level_risiko(nilai):
        if pd.isna(nilai):
            return "-"
        if nilai <= 5:
            return "Rendah"
        elif nilai <= 12:
            return "Menengah"
        else:
            return "Tinggi"

    df["Level Risiko BUMN"] = df["Skala Risiko BUMN"].apply(tentukan_level_risiko)

    df["Bulan Pelaporan"] = month_name[datetime.now().month]
    df["Tahun Pelaporan"] = datetime.now().year

    df["Justifikasi Skala Dampak"] = df.apply(justifikasi_dampak, axis=1)
    df["Justifikasi Skala Probabilitas"] = df.apply(justifikasi_prob, axis=1)
    df["Keterangan Skala Dampak"] = df.apply(lambda row: buat_keterangan_risiko(row, jenis="dampak"), axis=1)
    df["Keterangan Skala Probabilitas"] = df.apply(lambda row: buat_keterangan_risiko(row, jenis="prob"), axis=1)

 
    return df

def tampilkan_matriks_risiko(df, title="Heatmap Matriks Risiko Monitoring", x_label="Skala Dampak", y_label="Skala Probabilitas"):
    st.subheader(title)

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

    for _, row in df.iterrows():
        try:
            prob = int(row.get('Skala Probabilitas Saat Ini', 0))
            damp = int(row.get('Skala Dampak Saat Ini', 0))
            no_risiko = f"#{int(row['No'])}" if pd.notnull(row.get('No')) else ''
            i = prob - 1
            j = damp - 1
            if 0 <= i < 5 and 0 <= j < 5:
                existing = risk_matrix[i][j].replace("\n", ", ").split(", ") if risk_matrix[i][j] else []
                if no_risiko and no_risiko not in existing:
                    existing.append(no_risiko)
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
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)
    plt.tight_layout()
    st.pyplot(fig)

    return df



    return df
def simpan_data_monitoring():
    import os

    nama_bulan = month_name[datetime.now().month]
    tahun = datetime.now().year
    nama_file = f"monitoring_bulan_{nama_bulan}_{tahun}.xlsx"
    path_folder = "C:/saved"
    os.makedirs(path_folder, exist_ok=True)
    path_lengkap = os.path.join(path_folder, nama_file)

    with pd.ExcelWriter(path_lengkap, engine="xlsxwriter") as writer:
        # Simpan setiap tabel jika tersedia
        if "copy_update_program_mitigasi" in st.session_state:
            st.session_state["copy_update_program_mitigasi"].to_excel(writer, sheet_name="Program Mitigasi", index=False)

        if "copy_update_kri" in st.session_state:
            st.session_state["copy_update_kri"].to_excel(writer, sheet_name="KRI", index=False)

        if "copy_summary_rbb" in st.session_state:
            st.session_state["copy_summary_rbb"].to_excel(writer, sheet_name="Summary RBB", index=False)

        if "copy_tabel_residual_q1" in st.session_state:
            st.session_state["copy_tabel_residual_q1"].to_excel(writer, sheet_name="Residual Q1", index=False)

        if "copy_tabel_risiko_gabungan" in st.session_state:
            st.session_state["copy_tabel_risiko_gabungan"].to_excel(writer, sheet_name="Risiko Gabungan", index=False)

        if "copy_risiko_update_terpilih" in st.session_state:
            st.session_state["copy_risiko_update_terpilih"].to_excel(writer, sheet_name="Risiko Update Final", index=False)

    st.success(f"✅ File berhasil disimpan di `{path_lengkap}`")




def hapus_kolom_duplikat(df: pd.DataFrame, keep_cols=None) -> pd.DataFrame:
    if keep_cols is None:
        keep_cols = []

    kolom_unik = []
    kolom_isi = {}

    for col in df.columns:
        # Jangan hapus kolom yang wajib disimpan
        if col in keep_cols:
            kolom_unik.append(col)
            kolom_isi[col] = df[col]
            continue

        # Cek apakah sudah ada kolom dengan nama dan isi yang sama persis
        duplikat = False
        for col_eksisting, isi in kolom_isi.items():
            if col == col_eksisting and df[col].equals(isi):
                duplikat = True
                break

        if not duplikat:
            kolom_unik.append(col)
            kolom_isi[col] = df[col]

    return df[kolom_unik]
def tampilkan_rekap_gabungan_update_risiko_dengan_profil_interaktif(df_final: pd.DataFrame):
    st.subheader("📋 Rekap Gabungan Update Risiko + Informasi Perusahaan")

    # 🔢 Bulan dan Tahun
    bulan = month_name[datetime.now().month]
    tahun = datetime.now().year

    # 🏢 Informasi perusahaan
    df_info = st.session_state.get("copy_informasi_perusahaan", pd.DataFrame())
    info_dict = {}

    if isinstance(df_info, pd.DataFrame) and not df_info.empty:
        for _, row in df_info.iterrows():
            info_dict[row["Data yang dibutuhkan"]] = row["Input Pengguna"]

    # Tambahkan kolom informasi ke df_final
    df_final["Bulan Pelaporan"] = bulan
    df_final["Tahun Pelaporan"] = tahun
    df_final["Nama Perusahaan"] = info_dict.get("Nama Perusahaan", "")
    df_final["Alamat"] = info_dict.get("Alamat", "")
    df_final["Jenis Bisnis"] = info_dict.get("Jenis Bisnis", "")
    df_final["Direktorat"] = info_dict.get("Direktorat", "")
    df_final["Divisi"] = info_dict.get("Divisi", "")
    df_final["Departemen"] = info_dict.get("Departemen", "")

    # Susunan kolom
    kolom_tampilkan = [
        "Bulan Pelaporan", "Tahun Pelaporan",
        "Nama Perusahaan", "Alamat", "Jenis Bisnis", "Direktorat", "Divisi", "Departemen",
        "No", "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN", "Peristiwa Risiko", "Peristiwa Risiko dari Deskripsi",
        "Nilai Dampak", "Skala Dampak", "Nilai Eksposur Risiko",
        "Skala Dampak Q1", "Skala Q2_Dampak", "Skala Q3_Dampak", "Skala Q4_Dampak", "Skala Dampak Saat Ini",
        "Nilai Probabilitas", "Skala Probabilitas",
        "Skala Probabilitas Q1", "Skala Q2_Probabilitas", "Skala Q3_Probabilitas", "Skala Q4_Probabilitas", "Skala Prorbabilitas saat ini",
        "Jenis Program Dalam RKAP", "PIC", "Progress Program Mitigasi (%)",
        "Key Risk Indicators (KRI)", "Unit KRI", "KRI Aman", "KRI Hati-Hati", "KRI Bahaya", "KRI Saat Ini"
    ]

    for kol in kolom_tampilkan:
        if kol not in df_final.columns:
            df_final[kol] = ""

    with st.expander("🔍 Lihat/Edit Rekap Gabungan Monitoring"):
        edited_df = st.data_editor(df_final[kolom_tampilkan], use_container_width=True, num_rows="dynamic")

    if st.button("🔗 Integrasi"):
        simpan_integrasi_monitoring(edited_df)

def simpan_integrasi_monitoring(df: pd.DataFrame):
    import os

    # Ambil informasi dari kolom
    kode_perusahaan = df["Kode Perusahaan"].iloc[0] if "Kode Perusahaan" in df.columns else "NA"
    divisi = df["Divisi"].iloc[0] if "Divisi" in df.columns else "NA"
    departemen = df["Departemen"].iloc[0] if "Departemen" in df.columns else "NA"
    bulan = df["Bulan Pelaporan"].iloc[0] if "Bulan Pelaporan" in df.columns else month_name[datetime.now().month]
    tahun = df["Tahun Pelaporan"].iloc[0] if "Tahun Pelaporan" in df.columns else datetime.now().year

    # Bersihkan nama dari karakter yang tidak valid
    def bersihkan_nama(nama):
        return str(nama).replace(" ", "_").replace("/", "_")

    nama_file = f"integrasi_{bersihkan_nama(kode_perusahaan)}_{bersihkan_nama(divisi)}_{bersihkan_nama(departemen)}_{bulan}_{tahun}.xlsx"
    path_folder = "C:/integrasi"
    os.makedirs(path_folder, exist_ok=True)
    path_lengkap = os.path.join(path_folder, nama_file)

    try:
        with pd.ExcelWriter(path_lengkap, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Rekap Integrasi Monitoring", index=False)

        st.success("✅ File integrasi berhasil disimpan.")
        st.info(f"📁 Lokasi file: `{path_lengkap}`")
    except Exception as e:
        st.error("❌ Gagal menyimpan file integrasi.")
        st.warning(f"Detail error: {e}")

def justifikasi_dampak(row):
    biaya = row.get("Status Kinerja Biaya", "")
    pendapatan = row.get("Status Kinerja Pendapatan", "")
    if biaya == "Kurang" and pendapatan == "Kurang":
        return "Pencapaian pendapatan belum tercapai dan biaya melebihi batas bulanan."
    elif biaya == "Kurang":
        return "Biaya aktual melebihi batas bulanan."
    elif pendapatan == "Kurang":
        return "Pendapatan belum mencapai target bulanan."
    else:
        return "-"

def justifikasi_prob(row):
    mitigasi = row.get("Pengelolaan Mitigasi", "")
    kri = row.get("Pengelolaan KRI", "")
    if mitigasi == "Kurang" and kri == "Kurang":
        return "Progres mitigasi rendah dan KRI menunjukkan performa tidak aman."
    elif mitigasi == "Kurang":
        return "Progres program mitigasi masih di bawah target bulanan."
    elif kri == "Kurang":
        return "Indikator KRI menunjukkan performa yang tidak aman."
    else:
        return "-"

def buat_keterangan_risiko(row, jenis="dampak"):
    if jenis == "dampak":
        return justifikasi_dampak(row)
    elif jenis == "prob":
        return justifikasi_prob(row)
    return "-"

def main():
    st.title("📅 Monitoring & Evaluasi Risiko")

    # 📥 Multi-file uploader
    uploaded_files = st.file_uploader(
        "📥 Silakan unggah 3 file: Perlakuan Risiko, Profil Risiko,risk_based_budgeting",
        type=["xlsx"],
        accept_multiple_files=True
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            xls = pd.ExcelFile(uploaded_file)
            for sheet in xls.sheet_names:
                df = xls.parse(sheet)
                nama_session = sheet.lower().strip().replace(" ", "_")
                st.session_state[f"copy_{nama_session}"] = df

                if "anggaran pic" in sheet.lower():
                    st.session_state["copy_tabel_anggaran_pic"] = df

                elif "risiko gabungan" in sheet.lower() or "monitoring" in sheet.lower():
                    st.session_state["copy_tabel_risiko_gabungan"] = df

                elif "informasi perusahaan" in sheet.lower():
                    st.session_state["copy_informasi_perusahaan"] = df

        st.success("✅ File berhasil dimuat ke session state.")

    # 🗓️ Bulan dan tahun pelaporan
    bulan_saat_ini = datetime.now().month
    tahun_saat_ini = datetime.now().year
    nama_bulan = month_name[bulan_saat_ini]
    st.subheader(f"Bulan Pelaporan: {nama_bulan} {tahun_saat_ini}")

    # 🧩 Inisialisasi session state kosong jika belum ada
    for key in [
        "copy_tabel_risiko_gabungan",
        "copy_update_program_mitigasi",
        "copy_update_kri",
        "copy_summary_rbb",
        "copy_tabel_residual_q1",
        "copy_informasi_perusahaan"
    ]:
        st.session_state.setdefault(key, pd.DataFrame())

    # 🧠 Update user input
    tampilkan_update_program_mitigasi()
    tampilkan_update_kri()
    tampilkan_summary_rbb_dengan_pencapaian()

    # 🔁 Gabungan dan analisis
    df_final = tampilkan_gabungan_update_risiko()
    if df_final is None or df_final.empty:
        st.warning("⚠️ Data gabungan tidak tersedia atau kosong.")
        return

    # ✅ Simpan hasil analisis
    st.session_state["copy_risiko_update_terpilih"] = df_final

    # 🔥 Visualisasi heatmap
    tampilkan_matriks_risiko(df_final)

    # 📝 Keterangan
    with st.expander("📝 Tabel Keterangan Skala Dampak & Probabilitas"):
        if not df_final.empty:
            df_keterangan = pd.DataFrame({
                "Kode Risiko": df_final["Kode Risiko"],
                "Peristiwa Risiko": df_final["Peristiwa Risiko"],
                "Keterangan Skala Dampak": df_final["Keterangan Skala Dampak"],
                "Keterangan Skala Probabilitas": df_final["Keterangan Skala Probabilitas"]
            })
            st.dataframe(df_keterangan, use_container_width=True)
        else:
            st.info("ℹ️ Data belum tersedia.")

    # 🧾 Rekap akhir & ekspor
    st.markdown("## 🧾 Rekap Data Final")
    with st.expander("🔍 Lihat/Edit Rekap Gabungan Monitoring"):
        edited_df = st.data_editor(df_final, use_container_width=True, num_rows="dynamic")

    if st.button("📥 Update Rekap Gabungan"):
        st.session_state["copy_risiko_update_terpilih"] = edited_df
        st.success("✅ Data Rekap Gabungan diperbarui ke session.")

    if st.button("💾 Simpan Semua Data Monitoring"):
        simpan_data_monitoring()

    if st.button("🔗 Integrasi", key="integrasi_button_rekap"):
        simpan_integrasi_monitoring(edited_df)

    # 🏢 Tambahkan editor profil perusahaan dan rekap gabungan
    tampilkan_rekap_gabungan_update_risiko_dengan_profil_interaktif(df_final)
