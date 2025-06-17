import streamlit as st
import pandas as pd
import openai
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from calendar import month_name
from modules.utils import get_user_file
from modules.utils import get_user_folder, get_user_file
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

            # Load sheet ke session state
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

            if "informasi_perusahaan" in sheet_map:
                df = xls.parse(sheet_map["informasi_perusahaan"])
                if "Data yang dibutuhkan" in df.columns and "Input Pengguna" in df.columns:
                    st.session_state["copy_informasi_perusahaan"] = df

            if "copy_tabel_risiko_gabungan" not in st.session_state:
                if "copy_deskripsi_risiko" in st.session_state:
                    st.session_state["copy_tabel_risiko_gabungan"] = st.session_state["copy_deskripsi_risiko"].copy()

        except Exception as e:
            st.error(f"❌ Gagal membaca file: {file.name}")
            st.warning(f"Detail: {e}")
def gabungkan_semua_file_excel(uploaded_files, kolom_kunci="Kode Risiko"):
    df_gabungan = pd.DataFrame()
    data_profil = {}

    def proses_file(uploaded_file, filename):
        nonlocal data_profil
        try:
            xls = pd.ExcelFile(uploaded_file)
            all_sheets = []

            for sheet_name in xls.sheet_names:
                sheet_name_lc = sheet_name.strip().lower()
                sheet_key = sheet_name.strip().lower().replace(" ", "_")
                try:
                    df = xls.parse(sheet_name)
                    df.columns = df.columns.str.strip()

                    st.session_state[f"copy_{sheet_key}"] = df.copy()

                    # Tangani informasi_perusahaan
                    if sheet_name_lc == "informasi_perusahaan":
                        if {"Data yang dibutuhkan", "Input Pengguna"}.issubset(df.columns):
                            data_profil = pd.Series(
                                df["Input Pengguna"].values,
                                index=df["Data yang dibutuhkan"]
                            ).to_dict()
                        continue

                    # Tambahkan risiko jika kolom kunci ada
                    if kolom_kunci in df.columns:
                        df["Sheet Asal"] = sheet_name
                        df["File Asal"] = filename
                        all_sheets.append(df)

                except Exception as e:
                    st.warning(f"⚠️ Gagal memproses sheet '{sheet_name}' dari {filename}: {e}")
                    continue

            return pd.concat(all_sheets, ignore_index=True) if all_sheets else pd.DataFrame()

        except Exception as e:
            st.error(f"❌ Gagal membaca file {filename}: {e}")
            return pd.DataFrame()

    for uploaded_file in uploaded_files:
        filename = uploaded_file.name
        df_file = proses_file(uploaded_file, filename)
        df_gabungan = pd.concat([df_gabungan, df_file], ignore_index=True)

    if df_gabungan.empty:
        return pd.DataFrame()

    df_akhir = df_gabungan.groupby(kolom_kunci, dropna=False).agg(
        lambda x: x.dropna().iloc[0] if not x.dropna().empty else None
    ).reset_index()

    if data_profil:
        for kolom, nilai in data_profil.items():
            df_akhir[kolom] = nilai

    return df_akhir


def siapkan_residual_kuartalan():
    """
    Menyiapkan data residual Q1 dengan menggabungkan residual probabilitas dan dampak.
    Akan me-rename kolom kuartal agar sesuai format, serta memberikan peringatan jika kolom tidak ditemukan.
    """
    # Ambil dari session state
    df_prob = st.session_state.get("copy_tabel_residual_probabilitas", pd.DataFrame())
    df_dampak = st.session_state.get("copy_tabel_residual_dampak", pd.DataFrame())

    if df_prob.empty or df_dampak.empty:
        st.warning("⚠️ Data residual probabilitas atau dampak belum tersedia.")
        return pd.DataFrame()

    # Rename kolom agar sesuai downstream
    df_prob = df_prob.rename(columns={
        "Skala Q1": "Skala Q1_Probabilitas",
        "Skala Q2": "Skala Q2_Probabilitas",
        "Skala Q3": "Skala Q3_Probabilitas",
        "Skala Q4": "Skala Q4_Probabilitas"
    })

    df_dampak = df_dampak.rename(columns={
        "Skala Q1": "Skala Dampak Q1",
        "Skala Q2": "Skala Q2_Dampak",
        "Skala Q3": "Skala Q3_Dampak",
        "Skala Q4": "Skala Q4_Dampak"
    })

    # Validasi kolom yang wajib ada
    kolom_prob_rename = ["Skala Q1_Probabilitas", "Skala Q2_Probabilitas", "Skala Q3_Probabilitas", "Skala Q4_Probabilitas"]
    kolom_dampak_rename = ["Skala Dampak Q1", "Skala Q2_Dampak", "Skala Q3_Dampak", "Skala Q4_Dampak"]

    missing_prob = [k for k in kolom_prob_rename if k not in df_prob.columns]
    missing_dampak = [k for k in kolom_dampak_rename if k not in df_dampak.columns]

    if missing_prob or missing_dampak:
        st.warning(f"⚠️ Kolom residual berikut belum lengkap:\n- Probabilitas: {missing_prob}\n- Dampak: {missing_dampak}")
        return pd.DataFrame()

    # Merge berdasarkan Kode Risiko
    kolom_merge = ["Kode Risiko"]
    df_residual = pd.merge(
        df_prob[kolom_merge + kolom_prob_rename],
        df_dampak[kolom_merge + kolom_dampak_rename],
        on="Kode Risiko", how="outer"
    )

    # Simpan ke session state
    st.session_state["copy_tabel_residual_q1"] = df_residual.copy()
    return df_residual

            
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
    st.subheader("🛠️ Update Program Mitigasi --Silahkan isi!%--")

    # Coba ambil dari update sebelumnya
    df_update = st.session_state.get("copy_update_program_mitigasi", pd.DataFrame())
    df_sumber = df_update.copy()

    # Kalau belum ada update sebelumnya, ambil dari anggaran PIC
    if df_sumber.empty:
        df_pic = st.session_state.get("copy_tabel_anggaran_pic", pd.DataFrame())
        if df_pic.empty:
            st.warning("⚠️ Tidak ada data anggaran PIC atau program mitigasi yang tersedia.")
            return

        # Mapping kolom fleksibel
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
        df_sumber["Keterangan"] = ""

    else:
        # Pastikan kolom lengkap untuk editor
        if "Progress Program Mitigasi (%)" not in df_sumber.columns:
            df_sumber["Progress Program Mitigasi (%)"] = 0
        if "Keterangan" not in df_sumber.columns:
            df_sumber["Keterangan"] = ""

    # Tampilkan editor
    edited_df = st.data_editor(
        df_sumber,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_program_mitigasi"
    )

    if st.button("✅ Simpan Update Program Mitigasi"):
        update_program_mitigasi(edited_df)
        st.success("✅ Update Program Mitigasi disimpan.")


def tampilkan_update_kri():
    st.subheader("📈 Update (KRI)--Silahkan isi--")

    # Ambil dari update user sebelumnya kalau tersedia
    df_update = st.session_state.get("copy_update_kri", pd.DataFrame())
    df_sumber = df_update.copy()

    # Kalau tidak ada, gunakan data KRI lengkap
    if df_sumber.empty:
        df_kri = st.session_state.get("copy_key_risk_indicator", pd.DataFrame())
        if df_kri.empty:
            st.warning("⚠️ Tabel Key Risk Indicator belum tersedia di session state.")
            return

        # Mapping nama kolom fleksibel
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
        df_sumber["KRI Saat Ini"] = ""
        df_sumber["Pengelolaan KRI"] = ""

    else:
        # Tambahkan kolom jika belum tersedia
        if "KRI Saat Ini" not in df_sumber.columns:
            df_sumber["KRI Saat Ini"] = ""
        if "Pengelolaan KRI" not in df_sumber.columns:
            df_sumber["Pengelolaan KRI"] = ""

    # Tampilkan editor
    edited_df = st.data_editor(
        df_sumber,
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


# ------------------- UI: Ringkasan RBB + Pencapaian -------------------
def tampilkan_summary_rbb_dengan_pencapaian():
    st.subheader("📋Update Risk-Based Budgeting --Silahkan isi!--")

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


# ========================= FUNGSI PEMBANTU ========================= #

def merge_kri_mitigasi_residual(df):
    df_mitigasi = st.session_state.get("copy_update_program_mitigasi", pd.DataFrame())
    df_kri = st.session_state.get("copy_update_kri", pd.DataFrame())
    df_kri_lengkap = st.session_state.get("copy_key_risk_indicator", pd.DataFrame())
    df_residual = st.session_state.get("copy_tabel_residual_q1", pd.DataFrame())

    if not df_mitigasi.empty:
        kolom_mitigasi = ["Jenis Program Dalam RKAP", "PIC", "Progress Program Mitigasi (%)", "Keterangan"]
        df = df.drop(columns=[col for col in kolom_mitigasi if col in df.columns], errors="ignore")
        df = df.merge(df_mitigasi[["Kode Risiko"] + kolom_mitigasi].drop_duplicates(), on="Kode Risiko", how="left")

    if not df_kri.empty:
        kolom_kri = ["KRI Saat Ini", "Pengelolaan KRI"]
        df = df.drop(columns=[col for col in kolom_kri if col in df.columns], errors="ignore")
        df = df.merge(df_kri[["Kode Risiko"] + kolom_kri].drop_duplicates(), on="Kode Risiko", how="left")

    if not df_kri_lengkap.empty:
        kolom_kri_lengkap = ["Kode Risiko", "Key Risk Indicators (KRI)", "Unit KRI", "KRI Aman", "KRI Hati-Hati", "KRI Bahaya"]
        df = df.merge(df_kri_lengkap[kolom_kri_lengkap].drop_duplicates(), on="Kode Risiko", how="left")

    if not df_residual.empty:
        kolom_residual = [col for col in df_residual.columns if "Kode Risiko" in col or "Skala" in col]
        df = df.merge(df_residual[kolom_residual].drop_duplicates(), on="Kode Risiko", how="left")

    return df

def hitung_kinerja_keuangan(df):
    df_summary = st.session_state.get("copy_summary_rbb", pd.DataFrame())
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
    df["% Kinerja Keuangan"] = f"{persentase:.2f}%" if persentase else "-"

    bulan = datetime.now().month
    batas_biaya_bulanan = (nilai_biaya / 12) * bulan if nilai_biaya else 0
    batas_pendapatan_bulanan = (nilai_pendapatan / 12) * bulan if nilai_pendapatan else 0

    df["Status Kinerja Biaya"] = df["Pencapaian Biaya"].apply(lambda x: "Kurang" if x > batas_biaya_bulanan else "Cukup")
    df["Status Kinerja Pendapatan"] = df["Pencapaian Pendapatan"].apply(lambda x: "Kurang" if x < batas_pendapatan_bulanan else "Cukup")

    return df


def hitung_residual_bumn(df):
    bulan_saat_ini = datetime.now().month
    kuartal = (bulan_saat_ini - 1) // 3 + 1
    mapping_prob = {1: "Skala Probabilitas Q1", 2: "Skala Q2_Probabilitas", 3: "Skala Q3_Probabilitas", 4: "Skala Q4_Probabilitas"}
    mapping_dampak = {1: "Skala Dampak Q1", 2: "Skala Q2_Dampak", 3: "Skala Q3_Dampak", 4: "Skala Q4_Dampak"}

    kolom_prob = mapping_prob.get(kuartal, "Skala Probabilitas Q1")
    kolom_dampak = mapping_dampak.get(kuartal, "Skala Dampak Q1")

    df[kolom_prob] = pd.to_numeric(df.get(kolom_prob), errors="coerce")
    df[kolom_dampak] = pd.to_numeric(df.get(kolom_dampak), errors="coerce")

    def hitung_prob(row):
        val = row.get(kolom_prob)
        if pd.isna(val): return "-"
        if row.get("Pengelolaan KRI") == "Kurang" or row.get("Pengelolaan Mitigasi") == "Kurang":
            return min(val + 1, 5)
        return val

    def hitung_dampak(row):
        val = row.get(kolom_dampak)
        if pd.isna(val): return "-"
        if row.get("Status Kinerja Biaya") == "Kurang" or row.get("Status Kinerja Pendapatan") == "Kurang":
            return min(val + 1, 5)
        return val

    df["Skala Probabilitas Saat Ini"] = df.apply(hitung_prob, axis=1)
    df["Skala Dampak Saat Ini"] = df.apply(hitung_dampak, axis=1)
    df["Skala Risiko BUMN"] = pd.to_numeric(df["Skala Dampak Saat Ini"], errors="coerce") * pd.to_numeric(df["Skala Probabilitas Saat Ini"], errors="coerce")

    def level(val):
        if pd.isna(val): return "-"
        if val <= 5: return "Rendah"
        elif val <= 12: return "Menengah"
        else: return "Tinggi"

    df["Level Risiko BUMN"] = df["Skala Risiko BUMN"].apply(level)
    return df


def tambah_justifikasi_dan_keterangan(df):
    df["Bulan Pelaporan"] = month_name[datetime.now().month]
    df["Tahun Pelaporan"] = datetime.now().year
    df["Justifikasi Skala Dampak"] = df.apply(justifikasi_dampak, axis=1)
    df["Justifikasi Skala Probabilitas"] = df.apply(justifikasi_prob, axis=1)
    df["Keterangan Skala Dampak"] = df["Justifikasi Skala Dampak"]
    df["Keterangan Skala Probabilitas"] = df["Justifikasi Skala Probabilitas"]
    return df

# ========================= FUNGSIONALITAS UTAMA ========================= #

def generate_gabungan_risiko_final():
    """
    Membentuk df_final berisi informasi penting untuk analisis residual dan heatmap risiko.
    Menggabungkan data mitigasi, KRI, residual, serta kinerja keuangan yang mempengaruhi skala risiko.
    """
    df_risiko = st.session_state.get("copy_tabel_risiko_gabungan", pd.DataFrame())
    if df_risiko.empty:
        st.warning("⚠️ Data risiko gabungan belum tersedia.")
        return pd.DataFrame()

    # 🔁 Gabungkan data penting: KRI, mitigasi, residual
    df = merge_kri_mitigasi_residual(df_risiko.copy())

    # 🧮 Hitung kinerja keuangan & residual BUMN
    df = hitung_kinerja_keuangan(df)
    df = hitung_residual_bumn(df)

    # 📝 Justifikasi
    df["Justifikasi Skala Dampak"] = df.apply(justifikasi_dampak, axis=1)
    df["Justifikasi Skala Probabilitas"] = df.apply(justifikasi_prob, axis=1)

    # 🗓️ Metadata waktu pelaporan
    df["Bulan Pelaporan"] = month_name[datetime.now().month]
    df["Tahun Pelaporan"] = datetime.now().year

    # 🔎 Pilih hanya kolom penting untuk visualisasi & pelaporan risiko
    kolom_final = [
        "Kode Risiko", "Peristiwa Risiko",
        "Skala Probabilitas Saat Ini", "Skala Dampak Saat Ini",
        "Skala Risiko BUMN", "Level Risiko BUMN",
        "Justifikasi Skala Probabilitas", "Justifikasi Skala Dampak",
        "PIC", "Progress Program Mitigasi (%)",
        "KRI Saat Ini", "Pengelolaan KRI", "Pengelolaan Mitigasi",
        "Status Kinerja Biaya", "Status Kinerja Pendapatan", "% Kinerja Keuangan",
        "Bulan Pelaporan", "Tahun Pelaporan"
    ]

    # 💡 Ambil hanya kolom yang tersedia
    df = df[[col for col in kolom_final if col in df.columns]].copy()

    # 🔢 Tambah nomor urut
    df = df.reset_index(drop=True)
    df.insert(0, "No", df.index + 1)

    # 💾 Simpan ke session state
    st.session_state["copy_risiko_update_terpilih"] = df

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
def simpan_integrasi_monitoring_ke_server(df: pd.DataFrame):
    folder_simpan = "/app/data_integrasi"
    os.makedirs(folder_simpan, exist_ok=True)

    df_info = st.session_state.get("copy_informasi_perusahaan", pd.DataFrame())
    info_dict = {}
    if isinstance(df_info, pd.DataFrame) and not df_info.empty:
        required_cols = {"Data yang dibutuhkan", "Input Pengguna"}
        if required_cols.issubset(df_info.columns):
            for _, row in df_info.iterrows():
                info_dict[row["Data yang dibutuhkan"]] = row["Input Pengguna"]
        else:
            st.warning("⚠️ Kolom 'Data yang dibutuhkan' dan 'Input Pengguna' tidak lengkap dalam sheet profil.")
            return

    def safe_get_val(col, fallback="NA"):
        if col in df.columns:
            val = df[col].dropna().astype(str)
            if not val.empty:
                val0 = val.iloc[0].strip()
                return val0 if val0 else fallback
        return info_dict.get(col, fallback)

    from datetime import datetime

    kode_perusahaan = safe_get_val("Kode Perusahaan")
    divisi = safe_get_val("Divisi")
    departemen = safe_get_val("Departemen")
    tanggal_str = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

    def bersihkan_nama(nama):
        return str(nama).strip().replace(" ", "_").replace("/", "_").replace("\\", "_")

    nama_file = f"risk_monitoring__{bersihkan_nama(kode_perusahaan)}_{bersihkan_nama(divisi)}_{bersihkan_nama(departemen)}_{tanggal_str}.xlsx"
    path_lengkap = os.path.join(folder_simpan, nama_file)

    try:
        with pd.ExcelWriter(path_lengkap, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Rekap Integrasi Monitoring", index=False)

        st.success("✅ File integrasi monitoring berhasil disimpan ke server.")
        st.info(f"📁 Lokasi file: `{path_lengkap}`")
    except Exception as e:
        st.error("❌ Gagal menyimpan file integrasi monitoring.")
        st.warning(f"Detail error: {e}")
    
def simpan_dan_unduh_data_monitoring(df_integrasi: pd.DataFrame):
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    folder_local = "C:/saved"
    folder_integrasi = "/app/data_integrasi"

    if not os.path.exists(folder_local):
        os.makedirs(folder_local)
    os.makedirs(folder_integrasi, exist_ok=True)

    # Informasi fallback
    df_info = st.session_state.get("copy_informasi_perusahaan", pd.DataFrame())
    info_dict = {}
    if not df_info.empty:
        for _, row in df_info.iterrows():
            info_dict[row["Data yang dibutuhkan"]] = row["Input Pengguna"]

    for kol in ["Kode Perusahaan", "Divisi", "Departemen", "Bulan Pelaporan", "Tahun Pelaporan"]:
        if kol not in df_integrasi or df_integrasi[kol].dropna().eq("").all():
            df_integrasi[kol] = info_dict.get(kol, "")

    # Nama file
    def bersih(s): return str(s).strip().replace(" ", "_").replace("/", "_")
    kode = bersih(df_integrasi["Kode Perusahaan"].iloc[0])
    divisi = bersih(df_integrasi["Divisi"].iloc[0])
    dept = bersih(df_integrasi["Departemen"].iloc[0])
    bulan = bersih(df_integrasi["Bulan Pelaporan"].iloc[0] or month_name[datetime.now().month])
    tahun = str(df_integrasi["Tahun Pelaporan"].iloc[0] or datetime.now().year)

    filename = f"risk_monitoring_{kode}_{divisi}_{dept}_{bulan}_{tahun}_{timestamp}.xlsx"
    server_path = os.path.join(folder_local, f"monitoring_risiko_{timestamp}.xlsx")
    integrasi_path = os.path.join(folder_integrasi, filename)

    # Data tambahan untuk monitoring
    df_mitigasi = st.session_state.get("copy_update_program_mitigasi", pd.DataFrame())
    df_kri = st.session_state.get("copy_update_kri", pd.DataFrame())
    df_summary = st.session_state.get("copy_summary_rbb", pd.DataFrame())

    output = io.BytesIO()
    with pd.ExcelWriter(server_path, engine="xlsxwriter") as w1, \
         pd.ExcelWriter(output, engine="xlsxwriter") as w2, \
         pd.ExcelWriter(integrasi_path, engine="xlsxwriter") as w3:

        def simpan(df, sheet, writers):
            if not df.empty:
                for writer in writers:
                    df_out = df.copy()
                    if "Nomor" in df_out.columns:
                        df_out.drop(columns=["Nomor"], inplace=True)
                    df_out.insert(0, "Nomor", range(1, len(df_out)+1))
                    df_out.to_excel(writer, sheet_name=sheet, index=False)

        simpan(df_mitigasi, "Program Mitigasi", [w1, w2])
        simpan(df_kri, "KRI", [w1, w2])
        simpan(df_summary, "Summary RBB", [w1, w2])
        simpan(df_integrasi, "Rekap Integrasi Monitoring", [w1, w2, w3])

    output.seek(0)
    st.success("✅ File integrasi dan monitoring berhasil disimpan.")
    st.download_button(
        "⬇️ Unduh File Monitoring Risiko",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


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

def fallback_risiko_gabungan():
    """
    Mengisi session state 'copy_tabel_risiko_gabungan' dari sumber manapun yang tersedia.
    """
    kandidat_keys = [
        "copy_update_risk_details",
        "copy_deskripsi_risiko",
        "copy_risiko_update_terpilih",
        "copy_tabel_gabungan"
    ]

    for key in kandidat_keys:
        df = st.session_state.get(key, pd.DataFrame())
        if isinstance(df, pd.DataFrame) and not df.empty:
            if "Kode Risiko" in df.columns:
                st.session_state["copy_tabel_risiko_gabungan"] = df.copy()
                st.info(f"✅ Tabel risiko gabungan diambil dari `{key}`.")
                return
            else:
                st.warning(f"⚠️ Tabel `{key}` tidak memiliki kolom 'Kode Risiko'.")
def generate_tabel_data_integrasi():
    """
    Menggabungkan data dari copy_tabel_gabungan dan copy_risiko_update_terpilih 
    menjadi satu tabel data integrasi berdasarkan Kode Risiko.
    """
    df_gabungan = st.session_state.get("copy_tabel_gabungan", pd.DataFrame())
    df_final = st.session_state.get("copy_risiko_update_terpilih", pd.DataFrame())

    if df_gabungan.empty or df_final.empty:
        st.warning("⚠️ Data gabungan atau data final belum tersedia.")
        return pd.DataFrame()

    # Hindari kolom duplikat saat merge
    kolom_duplikat = [col for col in df_final.columns if col in df_gabungan.columns and col != "Kode Risiko"]
    df_gabungan_cleaned = df_gabungan.drop(columns=kolom_duplikat, errors="ignore")

    # Merge kedua DataFrame
    df_integrasi = pd.merge(
        df_gabungan_cleaned,
        df_final,
        on="Kode Risiko",
        how="left"
    )

    st.session_state["copy_tabel_data_integrasi"] = df_integrasi
    return df_integrasi

def main():
    st.title("📅 Monitoring & Evaluasi Risiko")

   


    # 📥 Upload file monitoring risiko
    uploaded_files = st.file_uploader(
        "Silahakan Unggah 4 file :Profil_Risiko,perlakuan_risiko,risk_based_budgeting,Residual_Dampak",
        type=["xlsx"],
        accept_multiple_files=True,
        key="upload_monitoring_semua"
    )

    if uploaded_files:
        upload_semua_file_monitoring(uploaded_files)
        df_gabungan = gabungkan_semua_file_excel(uploaded_files)
        if not df_gabungan.empty:
            st.session_state["copy_tabel_gabungan"] = df_gabungan
            st.success(f"✅ {len(df_gabungan)} risiko berhasil digabungkan (1 baris per risiko).")

            with st.expander("📄 Lihat Data Gabungan Awal", expanded=False):
                st.dataframe(df_gabungan, use_container_width=True)
                
    fallback_risiko_gabungan()
    siapkan_residual_kuartalan()

    st.session_state.setdefault("copy_update_program_mitigasi", pd.DataFrame())
    st.session_state.setdefault("copy_update_kri", pd.DataFrame())
    st.session_state.setdefault("copy_summary_rbb", pd.DataFrame())
    st.session_state.setdefault("copy_tabel_residual_q1", pd.DataFrame())

    st.subheader("🗓️ Pilih Bulan & Tahun Pelaporan")

    col1, col2 = st.columns(2)

    with col1:
        bulan_list = list(month_name)[1:]  # ['January', ..., 'December']
        bulan_default = datetime.now().month - 1
        bulan_pilihan = st.selectbox("Bulan Pelaporan", bulan_list, index=bulan_default, key="pilihan_bulan")

    with col2:
        tahun_saat_ini = datetime.now().year
        tahun_range = list(range(tahun_saat_ini - 5, tahun_saat_ini + 1))
        tahun_pilihan = st.selectbox("Tahun Pelaporan", tahun_range[::-1], key="pilihan_tahun")

    # Simpan ke session_state
    st.session_state["bulan_pelaporan"] = bulan_pilihan
    st.session_state["tahun_pelaporan"] = tahun_pilihan
    # 🔧 UI: Update risiko
    tampilkan_update_program_mitigasi()
    tampilkan_update_kri()
    tampilkan_summary_rbb_dengan_pencapaian()

    # ✅ Gabungkan semua risiko
    df_final = generate_gabungan_risiko_final()
    if df_final.empty:
        st.warning("⚠️ Data gabungan tidak tersedia atau kosong.")
        return
    st.session_state["copy_risiko_update_terpilih"] = df_final

    # 🔥 Heatmap
    tampilkan_matriks_risiko(df_final)

    # 📋 Justifikasi risiko
    with st.expander("📝 Tabel Keterangan Skala Dampak & Probabilitas"):
        st.dataframe(df_final[[
            "No", "Kode Risiko", "Peristiwa Risiko",
            "Justifikasi Skala Dampak", "Justifikasi Skala Probabilitas"
        ]], use_container_width=True)

    # ✏️ Editor risiko final
    st.markdown("## 🧾 Rekap Data Final")
    with st.expander("🔍 Lihat/Edit Rekap Gabungan Monitoring"):
        editor_key = "editor_data_integrasi"
        st.data_editor(
            df_final,
            use_container_width=True,
            num_rows="dynamic",
            key=editor_key
        )

    # 🔗 Tabel integrasi
    df_data_integrasi = generate_tabel_data_integrasi()
    if not df_data_integrasi.empty:
        st.markdown("## 🔗 Tabel Data Integrasi (Editable)")
        editor_key_integrasi = "editor_data_integrasi_final"
        edited_data = st.data_editor(
            df_data_integrasi,
            use_container_width=True,
            num_rows="dynamic",
            key=editor_key_integrasi
        )

        # Tombol update data integrasi
        if st.button("📥 Update Data Integrasi"):
            if isinstance(edited_data, list):
                df_integrasi = pd.DataFrame.from_records(edited_data)
            elif isinstance(edited_data, pd.DataFrame):
                df_integrasi = edited_data
            else:
                df_integrasi = pd.DataFrame()

            if not df_integrasi.empty:
                st.session_state["copy_tabel_data_integrasi"] = df_integrasi.copy()
                st.success("✅ Data integrasi berhasil diperbarui.")
            else:
                st.warning("⚠️ Data integrasi kosong atau belum diedit.")

        if st.button("💾 Simpan & Unduh Monitoring Risiko"):
            df_integrasi = st.session_state.get("copy_tabel_data_integrasi", pd.DataFrame())
            if not df_integrasi.empty:
                simpan_dan_unduh_data_monitoring(df_integrasi)
            else:
                st.warning("⚠️ Data integrasi belum tersedia untuk disimpan.")


if __name__ == "__main__":
    main()

