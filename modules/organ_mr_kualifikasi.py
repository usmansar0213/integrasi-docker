import streamlit as st 
import pandas as pd
import os

# ------------------------ Konfigurasi File ------------------------
FOLDER = "C:/saved"
FILE_PATH = os.path.join(FOLDER, "organ_mr_kualifikasi.xlsx")
FILE_ORGAN = os.path.join(FOLDER, "daftar_organ_mr.xlsx")  # ✅ Tambahkan baris ini


# ------------------------ Inisialisasi Data ------------------------
if not os.path.exists(FOLDER):
    os.makedirs(FOLDER)

if os.path.exists(FILE_PATH):
    df_laporan = pd.read_excel(FILE_PATH)
else:
    df_laporan = pd.DataFrame(columns=[
        "Perusahaan", "Tahun Awal Penugasan", "Nama", "Jabatan", "Unit", "Organ Risiko",
        "Pelatihan 1", "Jam 1", "Pelatihan 2", "Jam 2", "Total Jam", "Nama File Dokumen"
    ])

# ------------------------ Fungsi Lookup Kualifikasi ------------------------
def cari_kualifikasi_organ_pengelola(jenis_organ: str) -> str:
    jenis_organ = jenis_organ.strip().lower()

    kualifikasi_dict = {
        "dewan komisaris": """
### 🧾 Kualifikasi Dewan Komisaris / Dewan Pengawas
- **Pelatihan**:
  - Topik: risiko, fraud, bisnis, hukum, audit, dll
  - Min. 20 jam per tahun
  - PPL oleh lembaga terakreditasi
- **Sertifikasi**:
  - Min. 1 sertifikasi profesional (risiko, audit, hukum, keuangan)
  - Berlaku selama masa jabatan
""",
        "direksi": """
### 🧾 Kualifikasi Direksi
- **Pelatihan**:
  - Topik: risiko, fraud, hukum, audit, dll
  - Min. 40 jam per tahun
  - Min. 3 topik berbeda jika >1 tahun menjabat
- **Sertifikasi**:
  - Min. 1 sertifikasi relevan dengan bidang tugas
  - Berlaku selama masa jabatan
""",
        "direktur keuangan": """
### 🧾 Kualifikasi Direktur Keuangan (Lini Pertama)
- **Pelatihan**:
  - Topik: keuangan, audit, akuntansi
  - Min. 40 jam per tahun
  - 3 topik berbeda jika menjabat >1 tahun
- **Sertifikasi**:
  - Min. 1 sertifikasi keuangan/audit
""",
        "direktur risiko": """
### 🧾 Kualifikasi Direktur Risiko (Lini Kedua)
- **Pelatihan**:
  - Topik: risiko, audit, K3/HSSE, hukum
  - Min. 40 jam per tahun
  - Min. 3 topik berbeda jika menjabat >1 tahun
- **Sertifikasi**:
  - Min. 1 sertifikasi risiko/fraud/kepatuhan
""",
        "unit risiko": """
### 🧾 Kualifikasi Unit Kerja Manajemen Risiko
- **Pelatihan**:
  - Topik: risiko, fraud, audit, ESG, data analytics
  - Min. 60 jam per tahun
  - 3 topik berbeda jika menjabat >3 tahun
- **Sertifikasi**:
  - Min. 1 sertifikasi dalam tahun pertama
  - Total 3 sertifikasi jika >1 tahun
""",
        "komite audit": """
### 🧾 Kualifikasi Komite Audit (Non Dewan)
- **Pelatihan**:
  - Topik: audit, hukum, risiko, kepatuhan
  - Min. 20 jam per tahun
- **Sertifikasi**:
  - Sebelum menjabat: bidang sesuai
  - Saat menjabat: sertifikasi tambahan (audit/risk/hukum)
""",
        "komite pemantau risiko": """
### 🧾 Kualifikasi Komite Pemantau Risiko (Non Dewan)
- **Pelatihan**:
  - Topik: risiko, audit, HSSE, kepatuhan
  - Min. 20 jam per tahun
- **Sertifikasi**:
  - Wajib dimiliki sebelum menjabat
  - Sertifikasi tambahan saat menjabat
""",
        "komite tata kelola": """
### 🧾 Kualifikasi Komite Tata Kelola Terintegrasi
- **Pelatihan**:
  - Topik: tata kelola perusahaan
  - Min. 20 jam per tahun
- **Sertifikasi**:
  - Sertifikasi tata kelola saat menjabat
""",
        "spi": """
### 🧾 Kualifikasi SPI (Lini Ketiga)
- **Pelatihan**:
  - Kepala: 40 jam/tahun | Anggota: 20 jam/tahun
- **Sertifikasi**:
  - Min. 1 sertifikasi tahun pertama
  - Total 3 jika >1 tahun, topik audit/risiko
- **Syarat Integritas**:
  - Tidak pernah fraud, tidak rangkap jabatan
  - Objektif, independen, profesional
""",
        "unit pemilik risiko": """
### 🧾 Kualifikasi Unit Pemilik Risiko (Lini Pertama)
- **Pelatihan**:
  - Topik: manajemen risiko dan pengendalian internal
  - Min. 10 jam pelatihan setiap 2 tahun
  - Diikuti pimpinan unit & minimal 1 staf risiko
"""
    }

    return kualifikasi_dict.get(jenis_organ, "⚠️ Jenis organ tidak ditemukan. Silakan pilih dari menu yang tersedia.")

# ------------------------ UI Streamlit ------------------------

st.title("📘 Organ & Kualifikasi")
st.markdown("Petunjuk berdasarkan *SK-3/DKU.MBU/05/2023* – Kementerian BUMN")

# Tampilan informasi regulasi & tugas
with st.expander("📘 Acuan Regulasi: Organ Pengelola Risiko", expanded=False):
    st.markdown("""
**SK-3/DKU.MBU/05/2023** adalah Petunjuk Teknis (Juknis) yang ditetapkan oleh **Deputi Keuangan dan Manajemen Risiko Kementerian BUMN** untuk mengatur **komposisi dan kualifikasi** Organ Pengelola Risiko di lingkungan BUMN dan Anak Perusahaan.

### 🧾 Dasar Hukum
- **PER-2/MBU/03/2023** tentang Tata Kelola & Kegiatan Korporasi Signifikan
- Berlaku sejak **26 Mei 2023**
- Mengacu pada prinsip **Three Lines of Defense**:
    - **Lini 1:** Unit Pemilik Risiko (Owner Risiko)
    - **Lini 2:** Fungsi Risiko & Kepatuhan (Pengawasan Risiko)
    - **Lini 3:** Audit Internal / SPI (Penjaminan & Evaluasi)

### 🏛 Organ Pengelola Risiko & Tanggung Jawab
1. **Dewan Komisaris / Dewan Pengawas**  
   🔹 Mengawasi penerapan manajemen risiko & memberikan arahan.  
2. **Direksi**  
   🔹 Bertanggung jawab atas kebijakan risiko dan pelaksanaannya.  
3. **Komite Audit**  
   🔹 Memastikan efektivitas pengendalian internal & laporan keuangan.  
4. **Komite Pemantau Risiko**  
   🔹 Memantau kebijakan risiko & memberi rekomendasi mitigasi.  
5. **Komite Tata Kelola Terintegrasi**  
   🔹 Menjamin tata kelola terintegrasi dalam BUMN konglomerasi.  
6. **Direktur Risiko**  
   🔹 Menyusun kebijakan & metodologi manajemen risiko.  
7. **Direktur Keuangan**  
   🔹 Mengelola risiko keuangan secara terukur dan bertanggung jawab.  
8. **SPI (Satuan Pengawasan Intern)**  
   🔹 Melakukan audit internal untuk memastikan efektivitas pengendalian & pengelolaan risiko.

> 📌 Setiap organ wajib memenuhi **kualifikasi pelatihan dan sertifikasi profesional** sesuai perannya.
""")

# Pilihan dan hasil kualifikasi
pilihan = st.selectbox("🔍 Pilih Jenis Organ Pengelola Risiko:", [
    "Dewan Komisaris",
    "Direksi",
    "Direktur Keuangan",
    "Direktur Risiko",
    "Unit Risiko",
    "Komite Audit",
    "Komite Pemantau Risiko",
    "Komite Tata Kelola",
    "SPI",
    "Unit Pemilik Risiko"
])

hasil = cari_kualifikasi_organ_pengelola(pilihan)
st.markdown(hasil)

def load_laporan_data():
    if not os.path.exists(FOLDER):
        os.makedirs(FOLDER)
    if os.path.exists(FILE_PATH):
        return pd.read_excel(FILE_PATH)
    else:
        return pd.DataFrame(columns=[
            "Perusahaan", "Tahun Awal Penugasan", "Nama", "Jabatan", "Unit", "Organ Risiko"
       
        ])

# 4. Fungsi simpan file (bukti upload)
def simpan_file_bukti(file, perusahaan, nama, tahun):
    if file:
        filename = f"{perusahaan}_{nama}_{tahun}_{file.name}"
        save_path = os.path.join(FOLDER, filename)
        with open(save_path, "wb") as f:
            f.write(file.getbuffer())
        return filename
    return "-"

if "temp_kualifikasi_organ" not in st.session_state:
    st.session_state["temp_kualifikasi_organ"] = pd.DataFrame(columns=[
        "Perusahaan", "Tahun Awal Penugasan", "Nama", "Jabatan", "Unit", "Organ Risiko"
    ])
def load_daftar_organ():
    if os.path.exists(FILE_ORGAN):
        return pd.read_excel(FILE_ORGAN)
    else:
        return pd.DataFrame(columns=[
            "Perusahaan", "Tahun Awal Penugasan", "Nama", "Jabatan", "Unit", "Organ Risiko"
        ])

def save_daftar_organ(df):
    df.to_excel(FILE_ORGAN, index=False)

def modul_pendaftaran_organ():
    st.subheader("📑 Data Organ Pengelola Risiko")

    if "temp_kualifikasi_organ" not in st.session_state:
        st.session_state["temp_kualifikasi_organ"] = pd.DataFrame(columns=[
            "Perusahaan", "Tahun Awal Penugasan", "Nama", "Jabatan", "Unit", "Organ Risiko"
        ])

    df_temp = st.session_state["temp_kualifikasi_organ"]

    with st.expander("📥 Form Pengisian Organ", expanded=False):
        df_edit = st.data_editor(
            df_temp,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_pendaftaran_organ"
        )

        if st.button("💾 Simpan Data"):
            st.session_state["temp_kualifikasi_organ"] = df_edit.copy()

            df_lama = load_laporan_data()
            df_final = pd.concat([df_lama, df_edit], ignore_index=True)
            df_final.drop_duplicates(subset=["Perusahaan", "Tahun Awal Penugasan", "Nama"], inplace=True)
            df_final.to_excel(FILE_PATH, index=False)

            st.success("✅ Data berhasil disimpan.")
            st.info(f"📂 File disimpan di: `{FILE_PATH}`")

    # Tampilkan data lama
    df_laporan = load_laporan_data()
    with st.expander("📋 Data Organ Pengelola Risiko ", expanded=False):
        st.dataframe(df_laporan, use_container_width=True)

    # Tampilkan detail berdasarkan nama
    tampilkan_data_kualifikasi(df_laporan)

def tampilkan_data_kualifikasi(df_laporan: pd.DataFrame):
    st.subheader("📑 Data Kualifikasi Organ_MR")
    with st.expander("📄 Form Update Data Kualifikasi", expanded=False):

        if df_laporan.empty:
            st.info("📭 Belum ada data yang tersimpan.")
            return

        opsi_nama = df_laporan["Nama"].unique().tolist()
        nama_dipilih = st.selectbox("🧑 Pilih Nama", opsi_nama, key="lihat_detail_nama")

        data_terpilih = df_laporan[df_laporan["Nama"] == nama_dipilih]

        if not data_terpilih.empty:
            st.data_editor(data_terpilih.reset_index(drop=True), use_container_width=True, disabled=True)

            st.markdown("### 📝 Isian Data Kualifikasi Tambahan")

            perusahaan = data_terpilih["Perusahaan"].values[0]
            tahun = data_terpilih["Tahun Awal Penugasan"].values[0]

            col1, col2 = st.columns(2)
            with col1:
                nama_pelatihan = st.text_input("📚 Nama Pelatihan / Sertifikasi")
                jenis_pelatihan = st.selectbox("📌 Jenis", ["Pelatihan", "Sertifikasi"])
            with col2:
                jam = st.number_input("⏱️ Jumlah Jam", min_value=0, step=1, value=0)
                bulan_tahun = st.text_input("📅 Bulan_Tahun Pelatihan", placeholder="Misal: Maret 2025")

            nama_file = "-"
            bukti_dokumen = st.file_uploader("📎 Upload Bukti Dokumen", type=["pdf", "jpg", "png", "docx"])
            if bukti_dokumen:
                nama_file = f"{perusahaan}_{nama_dipilih}_{tahun}_{bukti_dokumen.name}"
                path_file = os.path.join(FOLDER, nama_file)
                with open(path_file, "wb") as f:
                    f.write(bukti_dokumen.getbuffer())
                st.success(f"✅ Dokumen disimpan di `{path_file}`")

            if st.button("🔄 Tambahkan ke Tabel Kualifikasi", key="tambah_kualifikasi"):
                data_baru = {
                    "Perusahaan": perusahaan,
                    "Tahun Awal Penugasan": tahun,
                    "Nama": nama_dipilih,
                    "Jabatan": data_terpilih["Jabatan"].values[0],
                    "Unit": data_terpilih["Unit"].values[0],
                    "Organ Risiko": data_terpilih["Organ Risiko"].values[0],
                    "Nama Pelatihan/Sertifikasi": nama_pelatihan,
                    "Jenis": jenis_pelatihan,
                    "Jam": jam,
                    "Bulan_Tahun Pelatihan": bulan_tahun,
                    "Nama File Dokumen": nama_file
                }

                st.session_state["data_kualifikasi"] = pd.concat([
                    st.session_state["data_kualifikasi"],
                    pd.DataFrame([data_baru])
                ], ignore_index=True)

                st.success("✅ Data ditambahkan ke tabel sementara.")


def modul_data_kualifikasi_langsung():
    with st.expander("📄 Data Kualifikasi Organ Risiko (Editable & Simpan)", expanded=False):

        file_kualifikasi = os.path.join(FOLDER, "Kualifikasi_organ_MR.xlsx")

        # 🔁 Inisialisasi atau load dari file hanya sekali di awal
        if "data_kualifikasi" not in st.session_state or st.session_state["data_kualifikasi"].empty:
            if os.path.exists(file_kualifikasi):
                df_awal = pd.read_excel(file_kualifikasi)
                st.session_state["data_kualifikasi"] = df_awal
            else:
                st.session_state["data_kualifikasi"] = pd.DataFrame(columns=[
                    "Perusahaan", "Tahun Awal Penugasan", "Nama", "Jabatan", "Unit", "Organ Risiko",
                    "Nama Pelatihan/Sertifikasi", "Jenis", "Jam", "Bulan_Tahun Pelatihan", "Nama File Dokumen"
                ])

        # ✅ Tampilkan tabel editable
        df_kualifikasi = st.session_state["data_kualifikasi"]

        df_edit = st.data_editor(
            df_kualifikasi,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_data_kualifikasi"
        )

        if st.button("💾 Simpan Seluruh Data Kualifikasi"):
            df_simpan = df_edit.copy()

            # Hitung ulang Total Jam jika ada kolom jam 1/jam 2
            if "Jam 1" in df_simpan.columns and "Jam 2" in df_simpan.columns:
                df_simpan["Total Jam"] = df_simpan[["Jam 1", "Jam 2"]].fillna(0).sum(axis=1)

            # Simpan ke folder C:/saved
            df_simpan.to_excel(file_kualifikasi, index=False)
            st.session_state["data_kualifikasi"] = df_simpan.copy()

            # Simpan juga ke folder integrasi dengan nama organ_timestamp.xlsx
            from datetime import datetime
            FOLDER_INTEGRASI = "C:/integrasi"
            if not os.path.exists(FOLDER_INTEGRASI):
                os.makedirs(FOLDER_INTEGRASI)

            timestamp = datetime.now().strftime("%d%m%y_%H%M%S")
            file_integrasi = os.path.join(FOLDER_INTEGRASI, f"organ_{timestamp}.xlsx")
            df_simpan.to_excel(file_integrasi, index=False)

            st.success("✅ Data berhasil disimpan ke dua lokasi.")
            st.info(f"📂 Disimpan di: `{file_kualifikasi}`")
            st.info(f"📂 Tersalin ke integrasi: `{file_integrasi}`")



def cek_organ_belum_lapor_kualifikasi():
    st.subheader("🔍 Organ Risiko yang Belum Melaporkan Pelatihan")

    df_laporan = load_laporan_data()
    df_kualifikasi = st.session_state.get("data_kualifikasi", pd.DataFrame())

    if df_laporan.empty:
        st.info("📭 Data Organ Pengelola Risiko belum tersedia.")
        return

    if df_kualifikasi.empty:
        st.warning("⚠️ Belum ada data kualifikasi yang masuk. Semua organ dianggap belum melapor.")
        df_belum_lapor = df_laporan.copy()
    else:
        # Buat kolom kunci gabungan untuk mencocokkan baris unik
        df_laporan["KEY"] = df_laporan["Perusahaan"].astype(str) + "|" + df_laporan["Nama"].astype(str) + "|" + df_laporan["Tahun Awal Penugasan"].astype(str)
        df_kualifikasi["KEY"] = df_kualifikasi["Perusahaan"].astype(str) + "|" + df_kualifikasi["Nama"].astype(str) + "|" + df_kualifikasi["Tahun Awal Penugasan"].astype(str)

        # Cari organ yang belum tercatat di data kualifikasi
        df_belum_lapor = df_laporan[~df_laporan["KEY"].isin(df_kualifikasi["KEY"])].drop(columns=["KEY"])

    if df_belum_lapor.empty:
        st.success("✅ Semua organ telah melaporkan pelatihannya.")
    else:
        st.warning(f"⚠️ Terdapat {len(df_belum_lapor)} organ yang belum melaporkan pelatihannya:")
        st.dataframe(df_belum_lapor, use_container_width=True)

def cek_kepatuhan_kualifikasi(df_kualifikasi: pd.DataFrame):
    st.subheader("🧾 Evaluasi Pemenuhan Kualifikasi Organ")

    # Struktur validasi syarat minimum
    kualifikasi_validasi = {
        "dewan komisaris": {"min_jam": 20, "sertifikasi_wajib": 1},
        "direksi": {"min_jam": 40, "sertifikasi_wajib": 1, "min_topik": 3},
        "direktur keuangan": {"min_jam": 40, "sertifikasi_wajib": 1, "min_topik": 3},
        "direktur risiko": {"min_jam": 40, "sertifikasi_wajib": 1, "min_topik": 3},
        "unit risiko": {"min_jam": 60, "sertifikasi_wajib": 1, "sertifikasi_total": 3, "min_topik": 3},
        "komite audit": {"min_jam": 20, "sertifikasi_wajib": 1},
        "komite pemantau risiko": {"min_jam": 20, "sertifikasi_wajib": 1},
        "komite tata kelola": {"min_jam": 20, "sertifikasi_wajib": 1},
        "spi": {"kepala_jam": 40, "anggota_jam": 20, "sertifikasi_total": 3},
        "unit pemilik risiko": {"min_jam": 10}
    }

    if df_kualifikasi.empty:
        st.info("📭 Belum ada data kualifikasi yang bisa dievaluasi.")
        return

    hasil_evaluasi = []

    grouped = df_kualifikasi.groupby(["Perusahaan", "Tahun Awal Penugasan", "Nama", "Jabatan", "Organ Risiko"])

    for (perusahaan, tahun, nama, jabatan, organ), group in grouped:
        organ_key = organ.strip().lower()
        validasi = kualifikasi_validasi.get(organ_key, {})

        total_jam = group["Jam"].sum()
        total_sertifikasi = group[group["Jenis"] == "Sertifikasi"].shape[0]
        total_topik = group["Nama Pelatihan/Sertifikasi"].nunique()

        status_jam = "✅"
        status_sertifikasi = "✅"
        status_topik = "✅"

        # Validasi jam
        if "kepala" in jabatan.lower() and organ_key == "spi":
            if total_jam < validasi.get("kepala_jam", 0):
                status_jam = "❌"
        elif "anggota" in jabatan.lower() and organ_key == "spi":
            if total_jam < validasi.get("anggota_jam", 0):
                status_jam = "❌"
        elif total_jam < validasi.get("min_jam", 0):
            status_jam = "❌"

        # Validasi sertifikasi
        if total_sertifikasi < validasi.get("sertifikasi_wajib", 0):
            status_sertifikasi = "❌"
        elif total_sertifikasi < validasi.get("sertifikasi_total", 0):
            status_sertifikasi = "❌"

        # Validasi topik
        if total_topik < validasi.get("min_topik", 0):
            status_topik = "❌"

        hasil_evaluasi.append({
            "Perusahaan": perusahaan,
            "Tahun": tahun,
            "Nama": nama,
            "Jabatan": jabatan,
            "Organ Risiko": organ,
            "Total Jam": total_jam,
            "Status Jam": status_jam,
            "Jumlah Sertifikasi": total_sertifikasi,
            "Status Sertifikasi": status_sertifikasi,
            "Jumlah Topik": total_topik,
            "Status Topik": status_topik
        })

    df_hasil = pd.DataFrame(hasil_evaluasi)
    st.dataframe(df_hasil, use_container_width=True)

def main():
    try:
        st.title("📘 Organ & Kualifikasi")

        # ======================= Upload Manual File Kualifikasi =======================
        st.markdown("### 📂 Upload File Kualifikasi Organ (opsional)")

        uploaded_file = st.file_uploader(
            "Unggah file Excel kualifikasi organ (.xlsx)",
            type=["xlsx"],
            key="upload_kualifikasi_file"
        )

        if uploaded_file is not None:
            try:
                df_uploaded = pd.read_excel(uploaded_file)
                st.session_state["data_kualifikasi"] = df_uploaded
                st.success(f"✅ File '{uploaded_file.name}' berhasil dimuat.")
            except Exception as e:
                st.error(f"❌ Gagal membaca file: {e}")
                
        st.markdown("Petunjuk berdasarkan *SK-3/DKU.MBU/05/2023* – Kementerian BUMN")

        # ✅ Tampilkan Expander Regulasi
        with st.expander("📘 Acuan Regulasi: Organ Pengelola Risiko", expanded=False):
            st.markdown("""
            **SK-3/DKU.MBU/05/2023** adalah Petunjuk Teknis (Juknis) yang ditetapkan oleh **Deputi Keuangan dan Manajemen Risiko Kementerian BUMN** untuk mengatur **komposisi dan kualifikasi** Organ Pengelola Risiko di lingkungan BUMN dan Anak Perusahaan.

            ### 🧾 Dasar Hukum
            - **PER-2/MBU/03/2023** tentang Tata Kelola & Kegiatan Korporasi Signifikan
            - Berlaku sejak **26 Mei 2023**
            - Mengacu pada prinsip **Three Lines of Defense**:
                - **Lini 1:** Unit Pemilik Risiko (Owner Risiko)
                - **Lini 2:** Fungsi Risiko & Kepatuhan (Pengawasan Risiko)
                - **Lini 3:** Audit Internal / SPI (Penjaminan & Evaluasi)

            ### 🏛 Organ Pengelola Risiko & Tanggung Jawab
            1. **Dewan Komisaris / Dewan Pengawas**  
               🔹 Mengawasi penerapan manajemen risiko & memberikan arahan.  
            2. **Direksi**  
               🔹 Bertanggung jawab atas kebijakan risiko dan pelaksanaannya.  
            3. **Komite Audit**  
               🔹 Memastikan efektivitas pengendalian internal & laporan keuangan.  
            4. **Komite Pemantau Risiko**  
               🔹 Memantau kebijakan risiko & memberi rekomendasi mitigasi.  
            5. **Komite Tata Kelola Terintegrasi**  
               🔹 Menjamin tata kelola terintegrasi dalam BUMN konglomerasi.  
            6. **Direktur Risiko**  
               🔹 Menyusun kebijakan & metodologi manajemen risiko.  
            7. **Direktur Keuangan**  
               🔹 Mengelola risiko keuangan secara terukur dan bertanggung jawab.  
            8. **SPI (Satuan Pengawasan Intern)**  
               🔹 Melakukan audit internal untuk memastikan efektivitas pengendalian & pengelolaan risiko.

            > 📌 Setiap organ wajib memenuhi **kualifikasi pelatihan dan sertifikasi profesional** sesuai perannya.
            """)

        # ✅ Pilihan jenis organ dan kualifikasi
        pilihan = st.selectbox("🔍 Pilih Jenis Organ Pengelola Risiko:", [
            "Dewan Komisaris",
            "Direksi",
            "Direktur Keuangan",
            "Direktur Risiko",
            "Unit Risiko",
            "Komite Audit",
            "Komite Pemantau Risiko",
            "Komite Tata Kelola",
            "SPI",
            "Unit Pemilik Risiko"
        ])

        hasil = cari_kualifikasi_organ_pengelola(pilihan)
        st.markdown(hasil)

        st.markdown("---")

        # ✅ Modul input data organ
        modul_pendaftaran_organ()

        # ✅ Modul input data kualifikasi
        modul_data_kualifikasi_langsung()

        st.markdown("---")

        # ✅ Cek Organ yang Belum Melapor
        st.subheader("🔎 Cek Pemenuhan")
        with st.expander("🔎 Cek Organ Belum Lapor Kualifikasi", expanded=False):
            cek_organ_belum_lapor_kualifikasi()

        # ✅ Evaluasi Kualifikasi jika data tersedia
        if "data_kualifikasi" in st.session_state and not st.session_state["data_kualifikasi"].empty:
            with st.expander("🔎 Evaluasi Kepatuhan Kualifikasi", expanded=False):
                cek_kepatuhan_kualifikasi(st.session_state["data_kualifikasi"])

    except Exception as e:
        st.error(f"❌ Terjadi error: {e}")


if __name__ == "__main__":
    main()
