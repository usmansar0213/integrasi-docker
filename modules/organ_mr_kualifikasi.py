from modules.utils import get_user_file
import streamlit as st 
import pandas as pd
import os
import datetime
from dotenv import load_dotenv
from datetime import datetime
import io

def upload_data_kualifikasi_saja():
    st.subheader("📥 Upload File Kualifikasi & Profil Perusahaan")

    col1, col2 = st.columns(2)

    # Uploader untuk data kualifikasi organ
    with col1:
        uploaded_kualifikasi = st.file_uploader(
            "📊 File Data Kualifikasi Organ (.xlsx)",
            type=["xlsx"],
            key="upload_kualifikasi"
        )
        if uploaded_kualifikasi:
            try:
                df = pd.read_excel(uploaded_kualifikasi)
                st.session_state["data_kualifikasi"] = df.copy()
                st.success(f"✅ Data kualifikasi dimuat dari: {uploaded_kualifikasi.name}")
            except Exception as e:
                st.error(f"❌ Gagal membaca file kualifikasi: {e}")

    # Uploader untuk profil perusahaan
    with col2:
        uploaded_profil = st.file_uploader(
            "🏢 File Profil Perusahaan (.xlsx)",
            type=["xlsx"],
            key="upload_profil_perusahaan"
        )
        if uploaded_profil:
            try:
                df_profil = pd.read_excel(uploaded_profil, sheet_name=None)
                # Coba cari sheet yang namanya mengandung "informasi"
                sheet_nama = next((s for s in df_profil if "informasi" in s.lower()), None)
                if sheet_nama:
                    df_info = df_profil[sheet_nama]
                    st.session_state["copy_informasi_perusahaan"] = df_info.copy()
                    st.success(f"✅ Data profil perusahaan dimuat dari sheet: {sheet_nama}")
                else:
                    st.warning("⚠️ Sheet dengan nama mengandung 'informasi' tidak ditemukan.")
            except Exception as e:
                st.error(f"❌ Gagal membaca file profil perusahaan: {e}")



def log_debug(pesan: str, filename: str = "log.txt"):
    """Mencatat pesan log dengan timestamp ke file log.txt"""
    folder = os.getenv("DATA_FOLDER", "/app/saved")  # Atau default folder Anda
    full_path = os.path.join(folder, filename)   
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(full_path, "a") as f:
            f.write(f"[{timestamp}] {pesan}\n")
    except Exception as e:
        st.warning(f"Gagal menulis log: {e}")

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

def modul_kualifikasi_organ():
    def on_select_organ():
        st.session_state["show_regulasi_expander"] = True

    st.markdown("Petunjuk berdasarkan *SK-3/DKU.MBU/05/2023* – Kementerian BUMN")

    if "show_regulasi_expander" not in st.session_state:
        st.session_state["show_regulasi_expander"] = False

    with st.expander("📘Organ Pengelola Risiko & Kualifikasi", expanded=st.session_state["show_regulasi_expander"]):
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
    ], key="organ_dipilih", on_change=on_select_organ)

    hasil = cari_kualifikasi_organ_pengelola(pilihan)
    st.markdown(hasil)


def simpan_file_bukti(file, perusahaan, nama, tahun):
    if file:
        filename = f"{perusahaan}_{nama}_{tahun}_{file.name}"
        save_path = os.path.join(FOLDER, filename)
        with open(save_path, "wb") as f:
            f.write(file.getbuffer())
        return filename
    return "-"
    
def simpan_kualifikasi_dengan_download():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_path = FOLDER  # Folder simpan global yang sudah diinisialisasi
    judul = "Kualifikasi_organ_MR"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filename = f"{judul}_{timestamp}.xlsx"
    server_file_path = os.path.join(folder_path, filename)
    output = io.BytesIO()

    df = st.session_state.get("data_kualifikasi", pd.DataFrame())

    if df.empty:
        st.warning("⚠️ Tidak ada data kualifikasi yang tersedia untuk disimpan.")
        return

    with pd.ExcelWriter(server_file_path, engine="xlsxwriter") as writer_server, \
         pd.ExcelWriter(output, engine="xlsxwriter") as writer_download:
        df.to_excel(writer_server, sheet_name="Kualifikasi", index=False)
        df.to_excel(writer_download, sheet_name="Kualifikasi", index=False)

    output.seek(0)

    st.success(f"✅ Data kualifikasi disimpan ke: `{server_file_path}`")
    st.download_button(
        label="⬇️ Unduh Data Kualifikasi",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def tampilkan_data_kualifikasi():
    st.subheader("📑 Update Kualifikasi ")
    df_kualifikasi = st.session_state.get("data_kualifikasi", pd.DataFrame())

    if df_kualifikasi.empty or "Nama" not in df_kualifikasi.columns:
        st.info("📭 Belum ada data kualifikasi yang tersedia atau kolom 'Nama' tidak ditemukan.")
        return

    opsi_nama = df_kualifikasi["Nama"].dropna().unique().tolist()
    if not opsi_nama:
        st.warning("⚠️ Kolom 'Nama' tersedia tapi tidak berisi data.")
        return

    nama_dipilih = st.selectbox("🧑 Pilih Nama", opsi_nama)
    data_terpilih = df_kualifikasi[df_kualifikasi["Nama"] == nama_dipilih]
    st.dataframe(data_terpilih, use_container_width=True)

    perusahaan = data_terpilih["Perusahaan"].values[0]
    tahun = data_terpilih["Tahun Awal Penugasan"].values[0]
    jabatan = data_terpilih["Jabatan"].values[0]
    unit = data_terpilih["Unit"].values[0]
    organ = data_terpilih["Organ Risiko"].values[0]

    col1, col2 = st.columns(2)
    with col1:
        nama_pelatihan = st.text_input("📚 Nama Pelatihan / Sertifikasi")
        jenis_pelatihan = st.selectbox("📌 Jenis", ["Pelatihan", "Sertifikasi"])
    with col2:
        jam = st.number_input("⏱️ Jumlah Jam", min_value=0, step=1)
        bulan_tahun = st.text_input("📅 Bulan_Tahun Pelatihan", placeholder="Misal: Maret 2025")

    bukti_dokumen = st.file_uploader("📎 Upload Bukti Dokumen", type=["pdf", "jpg", "png", "docx"])
    nama_file = "-"
    if bukti_dokumen:
        nama_file = simpan_file_bukti(bukti_dokumen, perusahaan, nama_dipilih, tahun)
        st.success(f"✅ Dokumen disimpan: {nama_file}")

    if st.button("➕ Tambahkan Data Kualifikasi"):
        data_baru = {
            "Perusahaan": perusahaan,
            "Tahun Awal Penugasan": tahun,
            "Nama": nama_dipilih,
            "Jabatan": jabatan,
            "Unit": unit,
            "Organ Risiko": organ,
            "Nama Pelatihan/Sertifikasi": nama_pelatihan,
            "Jenis": jenis_pelatihan,
            "Jam": jam,
            "Bulan_Tahun Pelatihan": bulan_tahun,
            "Nama File Dokumen": nama_file
        }

        st.session_state["data_kualifikasi"] = pd.concat([
            df_kualifikasi,
            pd.DataFrame([data_baru])
        ], ignore_index=True)
        st.success("✅ Data kualifikasi berhasil ditambahkan.")
        st.markdown("#### 📋 Tabel Kualifikasi Terbaru")
        st.dataframe(st.session_state["data_kualifikasi"], use_container_width=True)

def simpan_semua_kualifikasi_dengan_download():
    st.subheader("💾 Simpan & Unduh Semua Data Kualifikasi")

    df_kualifikasi = st.session_state.get("data_kualifikasi", pd.DataFrame())
    if df_kualifikasi.empty:
        st.warning("⚠️ Tidak ada data kualifikasi yang tersedia.")
        return

    # 🔄 Data Organ Belum Penuhi Jam Minimum
    grouped_min = df_kualifikasi.groupby(["Perusahaan", "Tahun Awal Penugasan", "Nama", "Jabatan", "Organ Risiko"])
    df_summary_min = grouped_min["Jam"].sum().reset_index()
    df_summary_min.rename(columns={"Jam": "Total Jam Pelatihan"}, inplace=True)
    df_belum_penuhi = df_summary_min[df_summary_min["Total Jam Pelatihan"] < 10]

    # 🔄 Evaluasi Kepatuhan (copy dari fungsi `cek_kepatuhan_kualifikasi`)
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

    hasil_evaluasi = []
    grouped_eval = df_kualifikasi.groupby(["Perusahaan", "Tahun Awal Penugasan", "Nama", "Jabatan", "Organ Risiko"])
    for (perusahaan, tahun, nama, jabatan, organ), group in grouped_eval:
        organ_key = organ.strip().lower()
        validasi = kualifikasi_validasi.get(organ_key, {})

        total_jam = group["Jam"].sum()
        total_sertifikasi = group[group["Jenis"] == "Sertifikasi"].shape[0]
        total_topik = group["Nama Pelatihan/Sertifikasi"].nunique()

        status_jam = "✅"
        status_sertifikasi = "✅"
        status_topik = "✅"

        if "kepala" in jabatan.lower() and organ_key == "spi":
            if total_jam < validasi.get("kepala_jam", 0):
                status_jam = "❌"
        elif "anggota" in jabatan.lower() and organ_key == "spi":
            if total_jam < validasi.get("anggota_jam", 0):
                status_jam = "❌"
        elif total_jam < validasi.get("min_jam", 0):
            status_jam = "❌"

        if total_sertifikasi < validasi.get("sertifikasi_wajib", 0):
            status_sertifikasi = "❌"
        elif total_sertifikasi < validasi.get("sertifikasi_total", 0):
            status_sertifikasi = "❌"

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

    df_evaluasi = pd.DataFrame(hasil_evaluasi)

    # ⏳ Siapkan file & unduhan
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"kualifikasi_risiko_{timestamp}.xlsx"
    file_path = os.path.join(FOLDER, filename)
    output = io.BytesIO()

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer_server, \
         pd.ExcelWriter(output, engine="xlsxwriter") as writer_download:
        df_kualifikasi.to_excel(writer_server, sheet_name="Data Kualifikasi", index=False)
        df_belum_penuhi.to_excel(writer_server, sheet_name="Belum Penuhi Jam", index=False)
        df_evaluasi.to_excel(writer_server, sheet_name="Evaluasi Kepatuhan", index=False)

        df_kualifikasi.to_excel(writer_download, sheet_name="Data Kualifikasi", index=False)
        df_belum_penuhi.to_excel(writer_download, sheet_name="Belum Penuhi Jam", index=False)
        df_evaluasi.to_excel(writer_download, sheet_name="Evaluasi Kepatuhan", index=False)

    output.seek(0)

    st.download_button(
        label="⬇️ Unduh Semua Data (3 Sheet)",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def modul_data_kualifikasi_langsung():
    st.subheader("📑 Update Organ MR ")
    with st.expander("📄 Data Kualifikasi Organ Risiko (Editable & Simpan)", expanded=False):
        file_kualifikasi = get_user_file("Kualifikasi_organ_MR.xlsx")

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
            simpan_data_kualifikasi(df_edit)

def simpan_data_kualifikasi(df_simpan):
    from datetime import datetime

    # Folder utama dan integrasi
    folder_saved = os.getenv("DATA_FOLDER", "/app/saved")  # pastikan volume Docker pakai /app/saved
    folder_integrasi = os.getenv("INTEGRASI_FOLDER", "/app/integrasi")  # volume untuk integrasi

    file_kualifikasi = get_user_file("Kualifikasi_organ_MR.xlsx")

    # Hitung ulang Total Jam jika ada kolom jam 1/jam 2
    if "Jam 1" in df_simpan.columns and "Jam 2" in df_simpan.columns:
        df_simpan["Total Jam"] = df_simpan[["Jam 1", "Jam 2"]].fillna(0).sum(axis=1)

    try:
        # ✅ Pastikan folder-folder aman
        os.makedirs(folder_saved, exist_ok=True)
        os.makedirs(folder_integrasi, exist_ok=True)

        # ✅ Simpan ke lokasi utama
        df_simpan.to_excel(file_kualifikasi, index=False, engine="openpyxl")
        st.session_state["data_kualifikasi"] = df_simpan.copy()
        st.session_state["df_kualifikasi_mr"] = df_simpan.copy()

        # ✅ Simpan juga ke folder integrasi dengan nama timestamp
        timestamp = datetime.now().strftime("%d%m%y_%H%M%S")
        file_integrasi = os.path.join(folder_integrasi, f"organ_{timestamp}.xlsx")
        df_simpan.to_excel(file_integrasi, index=False, engine="openpyxl")

        # ✅ Notifikasi sukses
        st.success("✅ Data berhasil disimpan ke dua lokasi.")
        st.info(f"📂 Disimpan di: `{file_kualifikasi}`")
        st.info(f"📂 Tersalin ke integrasi: `{file_integrasi}`")

    except Exception as e:
        st.error(f"❌ Gagal menyimpan data kualifikasi: {e}")
        if 'log_debug' in globals():
            log_debug(f"❌ Gagal simpan data kualifikasi: {e}")


def cek_organ_belum_lapor_kualifikasi():
    st.subheader("🔍 Organ Risiko dengan Pelatihan Minim")

    df_kualifikasi = st.session_state.get("data_kualifikasi", pd.DataFrame())

    if df_kualifikasi.empty:
        st.info("📭 Belum ada data kualifikasi yang tersedia.")
        return

    # Group by Nama & Tahun
    grouped = df_kualifikasi.groupby(["Perusahaan", "Tahun Awal Penugasan", "Nama", "Jabatan", "Organ Risiko"])
    summary = grouped["Jam"].sum().reset_index()
    summary.rename(columns={"Jam": "Total Jam Pelatihan"}, inplace=True)

    # Filter yang jam pelatihannya 0
    df_minim = summary[summary["Total Jam Pelatihan"] < 10]

    if df_minim.empty:
        st.success("✅ Semua organ telah memiliki pelatihan yang memadai.")
    else:
        st.warning(f"⚠️ Terdapat {len(df_minim)} individu dengan pelatihan < 10 jam:")
        st.dataframe(df_minim, use_container_width=True)


def cek_kepatuhan_kualifikasi():
    st.subheader("🧾 Evaluasi Pemenuhan Kualifikasi Organ")

    df_kualifikasi = st.session_state.get("data_kualifikasi", pd.DataFrame())

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
    
def simpan_kualifikasi_ke_server(df: pd.DataFrame):
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
    tanggal_jam_str = datetime.now().strftime("%d-%m-%Y_%H-%M")  # ← sekarang menyertakan jam dan menit

    def bersihkan_nama(nama):
        return str(nama).strip().replace(" ", "_").replace("/", "_").replace("\\", "_")

    nama_file = f"kualifikasi_{bersihkan_nama(kode_perusahaan)}_{bersihkan_nama(divisi)}_{bersihkan_nama(departemen)}_{tanggal_jam_str}.xlsx"
    path_lengkap = os.path.join(folder_simpan, nama_file)

    try:
        with pd.ExcelWriter(path_lengkap, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Kualifikasi", index=False)

        st.success("✅ File kualifikasi berhasil disimpan.")
        st.info(f"📁 Lokasi file: `{path_lengkap}`")
    except Exception as e:
        st.error("❌ Gagal menyimpan file kualifikasi.")
        st.warning(f"Detail error: {e}")


def main():
    st.title("📘 Kualifikasi Organ Pengelola Risiko")
    st.markdown("---")

    # Inisialisasi folder simpan
    load_dotenv()
    global FOLDER
    FOLDER = os.getenv("DATA_FOLDER", "/app/saved")
    os.makedirs(FOLDER, exist_ok=True)

    # 📥 Upload file utama kualifikasi
    with st.expander("📥 Upload File Kualifikasi Organ", expanded=True):
        upload_data_kualifikasi_saja()
    st.markdown("---")

    # Inisialisasi session jika belum ada
    if "data_kualifikasi" not in st.session_state:
        st.session_state["data_kualifikasi"] = pd.DataFrame(columns=[
            "Perusahaan", "Tahun Awal Penugasan", "Nama", "Jabatan", "Unit", "Organ Risiko",
            "Nama Pelatihan/Sertifikasi", "Jenis", "Jam", "Bulan_Tahun Pelatihan", "Nama File Dokumen"
        ])

    # === MODUL ACUAN & INPUT ===
    st.subheader("📘 Modul Acuan & Input Manual")
    modul_kualifikasi_organ()
    tampilkan_data_kualifikasi()
    modul_data_kualifikasi_langsung()
    st.markdown("---")

    # === ANALISIS PEMENUHAN ===
    st.subheader("🔍 Pemenuhan Kualifikasi")
    with st.expander("📋 Cek Organ Belum Penuhi Jam Minimum", expanded=False):
        cek_organ_belum_lapor_kualifikasi()

    with st.expander("🧾 Evaluasi Kepatuhan Kualifikasi", expanded=False):
        cek_kepatuhan_kualifikasi()
    st.markdown("---")

    # === SIMPAN FILE ===
    # === SIMPAN FILE MANUAL DENGAN TOMBOL ===
    df_kualifikasi = st.session_state.get("data_kualifikasi", pd.DataFrame())

    st.markdown("## 💾 Simpan & Unduh Data Kualifikasi")

    # Tombol simpan ke server integrasi
    if st.button("📤 Simpan ke Server Integrasi"):
        simpan_kualifikasi_ke_server(df_kualifikasi)

    # Tombol unduh file Excel 3-sheet
    simpan_semua_kualifikasi_dengan_download()

if __name__ == "__main__":
    main()