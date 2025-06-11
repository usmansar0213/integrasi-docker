import streamlit as st
import pandas as pd
import os
from datetime import datetime
from modules.utils import get_user_file
import io


# ------------------- Fungsi Inisialisasi Awal ------------------- #
def get_default_data():
    return {
        "informasi_perusahaan": pd.DataFrame({
            "Data yang dibutuhkan": [
                "Kode Perusahaan",
                "Nama Perusahaan",
                "Total Aset",
                "Alamat",
                "Jenis Bisnis",
                "Direktorat",
                "Divisi",
                "Departemen"
            ],
            "Input Pengguna": [""] * 8
        }),

        "pendapatan_bisnis_rutin": pd.DataFrame({
            "Kategori": ["Pendapatan Bisnis Rutin - 1"],
            "Nilai": [0.0]
        }),
        "pendapatan_bisnis_baru": pd.DataFrame({
            "Kategori": ["Pendapatan Bisnis Baru - 1"],
            "Nilai": [0.0]
        }),
        "biaya_rutin_bisnis_rutin": pd.DataFrame({
            "Kategori": ["Biaya Rutin Bisnis Rutin - 1"],
            "Nilai": [0.0]
        }),
        "biaya_non_rutin_bisnis_baru": pd.DataFrame({
            "Kategori": ["Biaya Non Rutin Bisnis Baru - 1"],
            "Nilai": [0.0]
        }),
    }



# ------------------- Fungsi Load Excel ------------------- #
def load_excel_data(uploaded_file):
    try:
        excel_data = pd.read_excel(uploaded_file, sheet_name=None)
        formatted_data = {}
        for sheet, df in excel_data.items():
            key = sheet.strip().lower().replace(" ", "_")
            formatted_data[key] = df
        return formatted_data
    except Exception as e:
        st.error(f"⚠️ Gagal memuat file Excel: {e}")
        return {}
def save_and_download_profil_perusahaan(daftar_tabel, kode_perusahaan):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Cek dan buat folder C:/saved
    folder_path = "C:/saved"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    if not kode_perusahaan:
        informasi_df = st.session_state.get("copy_informasi_perusahaan", pd.DataFrame())
        if not informasi_df.empty:
            try:
                kode_row = informasi_df[informasi_df["Data yang dibutuhkan"] == "Kode Perusahaan"]
                if not kode_row.empty:
                    kode_perusahaan = kode_row.iloc[0]["Input Pengguna"]
            except Exception as e:
                st.warning(f"⚠️ Gagal mengambil Kode Perusahaan dari Informasi Perusahaan: {e}")
        if not kode_perusahaan:
            kode_perusahaan = "UnknownCompany"

    server_file_path = os.path.join(folder_path, f"Profil_Perusahaan_{kode_perusahaan}_{timestamp}.xlsx")
    output = io.BytesIO()

    try:
        with pd.ExcelWriter(server_file_path, engine='xlsxwriter') as writer_server, \
             pd.ExcelWriter(output, engine='xlsxwriter') as writer_download:

            # 1. Sheet pertama tetap "Kode Perusahaan" (khusus)
            df_kode = pd.DataFrame([[kode_perusahaan]], columns=["Kode Perusahaan"])
            df_kode.to_excel(writer_server, sheet_name="Kode Perusahaan", index=False)
            df_kode.to_excel(writer_download, sheet_name="Kode Perusahaan", index=False)

            # 2. Save semua tabel copy_* lain ke sheet masing-masing
            for key in st.session_state.keys():
                if key.startswith("copy_"):
                    df_to_save = st.session_state[key]
                    if isinstance(df_to_save, pd.DataFrame) and not df_to_save.empty:
                        sheet_name = key.replace("copy_", "")  # Nama sheet
                        if sheet_name.lower() != "kode_perusahaan":  # Hindari double save
                            sheet_name = sheet_name[:31]  # Limit nama sheet 31 karakter
                            df_to_save.to_excel(writer_server, sheet_name=sheet_name, index=False)
                            df_to_save.to_excel(writer_download, sheet_name=sheet_name, index=False)

        output.seek(0)
        st.download_button(
            label="⬇️ Unduh Data Profil Perusahaan",
            data=output,
            file_name=f"Profil_Perusahaan_{kode_perusahaan}_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Gagal menyimpan file: {e}")



# ------------------- Fungsi Utama Modul ------------------- #
def modul_profil_perusahaan():
    default_data = get_default_data()

    # E - Establishment (Sekali saja saat kosong)
    for tabel, df in default_data.items():
        key = f"copy_{tabel}"
        if key not in st.session_state or not isinstance(st.session_state[key], pd.DataFrame) or st.session_state[key].empty:
            st.session_state[key] = df.copy()

    # L - Load file jika ada
    uploaded_file = st.file_uploader("📂 Pilih file Excel", type=["xls", "xlsx"])
    if uploaded_file:
        excel_data = load_excel_data(uploaded_file)
        for sheet_name, df in excel_data.items():
            st.session_state[f"copy_{sheet_name}"] = df.copy()

    # T - Tampilkan semua editor
    for tabel in default_data:
        st.subheader(f"📋 {tabel.replace('_', ' ').title()}")
        key_copy = f"copy_{tabel}"
        key_temp = f"temp_{tabel}"

        df_awal = st.session_state[key_copy].copy()

        # Khusus untuk informasi_perusahaan: pastikan kolom wajib ada
        if tabel == "informasi_perusahaan":
            kolom_wajib = default_data[tabel]["Data yang dibutuhkan"].tolist()

            # Tambahkan "💰 Total Aset" setelah "Nama Perusahaan"
            if "Total Aset" not in kolom_wajib:
                kolom_wajib.insert(kolom_wajib.index("Nama Perusahaan") + 1, "Total Aset")

            existing_df = df_awal
            for kolom in kolom_wajib:
                if kolom not in existing_df["Data yang dibutuhkan"].values:
                    df_awal = pd.concat([
                        existing_df,
                        pd.DataFrame({"Data yang dibutuhkan": [kolom], "Input Pengguna": [""]})
                    ], ignore_index=True)

            urutan_map = {nama: i for i, nama in enumerate(kolom_wajib)}
            df_awal["urut"] = df_awal["Data yang dibutuhkan"].apply(lambda x: urutan_map.get(x, 99))
            df_awal = df_awal.sort_values("urut").drop(columns="urut").reset_index(drop=True)


        # Simpan ke temp editor
        df_temp = st.data_editor(
            df_awal,
            key=f"editor_{tabel}",
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic"
        )
        st.session_state[key_temp] = df_temp.copy()

    # Di dalam modul_profil_perusahaan() tambahkan tombol baru:
    if st.button("Update Data"):
        # Otomatis Update Semua Data dulu
        for tabel in default_data:
            key_copy = f"copy_{tabel}"
            key_temp = f"temp_{tabel}"

            if key_temp in st.session_state:
                df_temp = st.session_state[key_temp]
                if isinstance(df_temp, pd.DataFrame) and not df_temp.empty:
                    st.session_state[key_copy] = df_temp.copy()

        # Ambil Kode Perusahaan terbaru
        informasi_df = st.session_state.get("copy_informasi_perusahaan", pd.DataFrame())
        kode_perusahaan = ""
        if not informasi_df.empty:
            kode_row = informasi_df[informasi_df["Data yang dibutuhkan"] == "Kode Perusahaan"]
            if not kode_row.empty:
                kode_perusahaan = kode_row.iloc[0]["Input Pengguna"]

        save_and_download_profil_perusahaan(default_data.keys(), kode_perusahaan)


# ------------------- Main ------------------- #
def main():
    st.title("🛡️ Profil Perusahaan")
    modul_profil_perusahaan()

if __name__ == "__main__":
    main()