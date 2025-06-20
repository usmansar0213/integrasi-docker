import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import io

# -------------------- Gabungkan file Excel dari uploader --------------------
def gabungkan_file_excel(uploaded_files):
    df_gabungan = pd.DataFrame()
    daftar_sheet = {}
    perusahaan_terdeteksi = set()
    progress_bar = st.progress(0, text="⏳ Menggabungkan data...")

    for i, uploaded_file in enumerate(uploaded_files):
        try:
            file_name = uploaded_file.name
            df_excel = pd.read_excel(uploaded_file, sheet_name=None)

            for sheetname, df_sheet in df_excel.items():
                df_sheet = df_sheet.copy()
                if {"Kode Risiko", "Kode Perusahaan"}.issubset(df_sheet.columns):
                    df_sheet["Nama File"] = file_name
                    df_sheet["Sheet"] = sheetname
                    perusahaan_terdeteksi.update(df_sheet["Kode Perusahaan"].dropna().unique())
                    df_gabungan = pd.concat([df_gabungan, df_sheet], ignore_index=True)

                    if sheetname not in daftar_sheet:
                        daftar_sheet[sheetname] = df_sheet
                    else:
                        daftar_sheet[sheetname] = pd.concat([daftar_sheet[sheetname], df_sheet], ignore_index=True)
        except Exception as e:
            st.error(f"❌ Gagal membaca file `{uploaded_file.name}`: {e}")

        progress_bar.progress((i + 1) / len(uploaded_files), text=f"📄 Memproses: {uploaded_file.name}")

    return df_gabungan, daftar_sheet, perusahaan_terdeteksi

# -------------------- Normalisasi Nama Bulan --------------------
def normalisasi_bulan(bulan_input):
    mapping = {
        "januari": "january", "februari": "february", "maret": "march",
        "april": "april", "mei": "may", "juni": "june", "juli": "july",
        "agustus": "august", "september": "september", "oktober": "october",
        "november": "november", "desember": "december"
    }
    return mapping.get(bulan_input.lower(), bulan_input.lower())

# -------------------- Pecah Nama File --------------------
def pecah_nama_file(nama_file):
    nama_file = os.path.splitext(os.path.basename(nama_file))[0]
    pattern = r"risk_monitoring__([A-Z0-9]+)_[A-Z0-9]+_[A-Z0-9]+_([A-Za-z]+)_([0-9]{4})"
    match = re.match(pattern, nama_file, re.IGNORECASE)
    if match:
        return {
            "perusahaan": match.group(1).upper(),
            "bulan": match.group(2).capitalize(),
            "tahun": match.group(3)
        }
    return None

# -------------------- Tampilkan Tabel Rekap Nama File --------------------
def tampilkan_tabel_pecahan_nama_file(semua_file):
    data = []
    for file in semua_file:
        hasil = pecah_nama_file(file)
        if hasil:
            hasil["nama_file"] = os.path.basename(file)
            data.append(hasil)

    if data:
        st.subheader("📋 Rekap File")
        st.dataframe(pd.DataFrame(data))
    else:
        st.info("Tidak ada file yang sesuai format penamaan integrasi.")

# -------------------- Cek Perusahaan Belum Kirim --------------------
def cek_perusahaan_tanpa_file(semua_file, daftar_perusahaan, bulan, tahun):
    perusahaan_ada_file = set()
    st.caption(f"📆 Bulan: {bulan} | Tahun: {tahun}")

    for file in semua_file:
        hasil = pecah_nama_file(file)
        if hasil:
            if hasil["bulan"].lower() == normalisasi_bulan(bulan).lower() and hasil["tahun"] == tahun:
                perusahaan_ada_file.add(hasil["perusahaan"])

    belum_lapor = sorted(set(daftar_perusahaan) - perusahaan_ada_file)
    if belum_lapor:
        st.warning(f"🚫 {len(belum_lapor)} perusahaan belum mengirim file integrasi untuk {bulan} {tahun}:")
        df_belum_lapor = pd.DataFrame([{
            "Kode Perusahaan": kode,
            "Bulan": bulan,
            "Tahun": tahun
        } for kode in belum_lapor])
        st.dataframe(df_belum_lapor)

# -------------------- Cek Perusahaan Tidak Terdaftar --------------------
def cek_perusahaan_tidak_terdaftar(df_gabungan, daftar_perusahaan):
    if "Kode Perusahaan" not in df_gabungan.columns:
        st.warning("⚠️ Kolom 'Kode Perusahaan' tidak ditemukan dalam data gabungan.")
        return
    perusahaan_di_data = set(df_gabungan["Kode Perusahaan"].dropna().unique())
    perusahaan_input = set(daftar_perusahaan)
    perusahaan_tidak_terdaftar = sorted(perusahaan_di_data - perusahaan_input)
    if perusahaan_tidak_terdaftar:
        st.warning(f"🚫 {len(perusahaan_tidak_terdaftar)} perusahaan TIDAK TERDAFTAR tapi ada filenya:")
        st.write(perusahaan_tidak_terdaftar)
    else:
        st.success("✅ Tidak ditemukan perusahaan di luar daftar yang kamu inputkan.")

# -------------------- Fungsi Utama --------------------
def main():
    st.header("🧩 Modul Integrasi Data")

    uploaded_files = st.file_uploader(
        "📤 Unggah file Monitoring",
        type=["xlsx"],
        accept_multiple_files=True,
        key="upload_file_integrasi"
    )

    if not uploaded_files:
        st.warning("📤 Silakan unggah minimal 1 file Excel untuk melanjutkan analisis.")
        return

    daftar_perusahaan = [
        kode.strip().upper()
        for kode in st.text_input(
            "📛 Masukkan daftar kode perusahaan wajib (pisahkan dengan koma)",
            value="PLND, PWR, DPK, EBT, CORP"
        ).split(",")
        if kode.strip()
    ]

    bulan = st.selectbox("📅 Pilih Bulan", [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ], index=datetime.now().month - 1)

    tahun = st.text_input("📆 Tahun", value=str(datetime.now().year))

    semua_file_names = [f.name for f in uploaded_files]
    df_gabungan, daftar_sheet, perusahaan_terdeteksi = gabungkan_file_excel(uploaded_files)

    # Simpan hasil integrasi ke memory (BytesIO)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nama_file_integrasi = f"data_integrasi_risiko_{timestamp}.xlsx"
    output = io.BytesIO()

    try:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_gabungan.to_excel(writer, index=False, sheet_name="Gabungan")
            for sheetname, df_sheet in daftar_sheet.items():
                df_sheet.to_excel(writer, index=False, sheet_name=sheetname[:31])
        st.success(f"✅ Data berhasil diintegrasikan. Jumlah total baris: {len(df_gabungan)}")
        st.dataframe(df_gabungan.head())

        st.download_button(
            label="⬇️ Unduh Hasil Integrasi",
            data=output.getvalue(),
            file_name=nama_file_integrasi,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"❌ Gagal menyimpan file integrasi: {e}")

    # Analisis tambahan
    tampilkan_tabel_pecahan_nama_file(semua_file_names)
    cek_perusahaan_tanpa_file(semua_file_names, daftar_perusahaan, bulan, tahun)
    cek_perusahaan_tidak_terdaftar(df_gabungan, daftar_perusahaan)

# -------------------- Jalankan Aplikasi --------------------
if __name__ == "__main__":
    main()
