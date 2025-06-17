
import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# ======================= KONFIGURASI =======================
NAMA_TABEL = "loss_event"
BASE_FOLDER = "loss_event"  # 💡 Folder lokal (relatif)
LAMPIRAN_FOLDER = os.path.join(BASE_FOLDER, "lampiran")
RECORD_FILE = os.path.join(BASE_FOLDER, "loss_event_record.xlsx")

# ======================= (L) LOAD FILE =======================
def load_file_loss_event():
    os.makedirs(BASE_FOLDER, exist_ok=True)
    if os.path.exists(RECORD_FILE):
        try:
            df = pd.read_excel(RECORD_FILE)
            st.session_state[f"copy_{NAMA_TABEL}"] = df.copy()
            st.success(f"✅ Data berhasil dimuat dari: {RECORD_FILE}")
        except Exception as e:
            st.error(f"❌ Gagal membaca file: {e}")
            st.session_state[f"copy_{NAMA_TABEL}"] = pd.DataFrame()
    else:
        st.info("📁 Belum ada file loss_event_record.xlsx. Akan dibuat saat simpan pertama.")
        st.session_state[f"copy_{NAMA_TABEL}"] = pd.DataFrame()

# ======================= (E) ESTABLISH SESSION =======================
def init_loss_event():
    if f"copy_{NAMA_TABEL}" not in st.session_state:
        st.session_state[f"copy_{NAMA_TABEL}"] = pd.DataFrame()
    if f"temp_{NAMA_TABEL}" not in st.session_state:
        st.session_state[f"temp_{NAMA_TABEL}"] = {}
    if f"update_{NAMA_TABEL}" not in st.session_state:
        st.session_state[f"update_{NAMA_TABEL}"] = False

# ======================= SIMPAN LAMPIRAN FILE =======================
def simpan_lampiran(file, prefix):
    if file:
        os.makedirs(LAMPIRAN_FOLDER, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_name = f"{prefix}_{timestamp}_{file.name.replace(' ', '_')}"
        file_path = os.path.join(LAMPIRAN_FOLDER, safe_name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())
        return safe_name
    return None

# ======================= (T + A) FORM INPUT =======================
def form_loss_event():
    temp = st.session_state[f"temp_{NAMA_TABEL}"]

    st.markdown("### 📝 Form Input Kejadian Kerugian (Loss Event)")
    
    # GANTI TANGGAL KE TEKS
    temp["Tanggal"] = st.text_input("📅 Tanggal Kejadian (bebas format, contoh: 13 April 2025)", value=temp.get("Tanggal", ""))

    temp["Lokasi"] = st.text_input("📍 Lokasi Kejadian", value=temp.get("Lokasi", ""))
    temp["Deskripsi"] = st.text_area("📝 Deskripsi Kejadian", value=temp.get("Deskripsi", ""))
    temp["Kategori"] = st.selectbox("📂 Kategori", ["Fisik", "Keuangan", "SDM", "Teknologi"])
    temp["Sumber"] = st.selectbox("🏷️ Sumber Penyebab", ["Internal", "Eksternal", "Force Majeure"])
    temp["Penyebab"] = st.text_area("⚠️ Penyebab Kejadian", value=temp.get("Penyebab", ""))
    temp["Kronologis"] = st.text_area("📖 Kronologis", value=temp.get("Kronologis", ""))
    temp["Penanganan"] = st.text_area("🛠️ Penanganan Saat Kejadian", value=temp.get("Penanganan", ""))
    temp["Kelompok"] = st.selectbox("🧾 Kelompok", ["Kecelakaan", "Kerusakan", "Kesalahan Prosedur"])
    temp["Subkelompok"] = st.selectbox("📑 Subkelompok", ["Patah", "Tabrakan", "Kelalaian", "Lainnya"])

    temp["Kerugian"] = st.number_input("💰 Nilai Kerugian", min_value=0)
    temp["Berulang"] = st.selectbox("🔁 Kejadian Berulang?", ["Tidak", "Ya"])
    temp["Frekuensi"] = st.number_input("📅 Frekuensi (1 Tahun)", min_value=0, value=1)
    temp["Mitigasi"] = st.text_area("🧩 Mitigasi Direncanakan", value=temp.get("Mitigasi", ""))
    temp["Realisasi"] = st.text_area("✅ Realisasi Mitigasi", value=temp.get("Realisasi", ""))
    temp["Perbaikan"] = st.text_area("🔧 Perbaikan Mendatang", value=temp.get("Perbaikan", ""))

    temp["Pihak"] = st.text_area("👥 Pihak Terkait", value=temp.get("Pihak", ""))
    temp["Asuransi"] = st.selectbox("🛡️ Ada Asuransi?", ["Tidak", "Ya"])
    temp["Premi"] = st.number_input("💸 Premi", min_value=0)
    temp["Klaim"] = st.number_input("💸 Klaim Diajukan", min_value=0)
    temp["Biaya"] = st.number_input("💸 Biaya Tindak Lanjut", min_value=0)

    kejadian_file = st.file_uploader("📁 Lampiran Kejadian", type=["pdf", "jpg", "png"])
    dampak_file = st.file_uploader("📁 Lampiran Dampak", type=["pdf", "jpg", "png"])
    tindak_file = st.file_uploader("📁 Lampiran Tindak Lanjut", type=["pdf", "jpg", "png"])

    temp["Lampiran_Kejadian"] = simpan_lampiran(kejadian_file, "Kejadian")
    temp["Lampiran_Dampak"] = simpan_lampiran(dampak_file, "Dampak")
    temp["Lampiran_Tindak_Lanjut"] = simpan_lampiran(tindak_file, "Tindak")

    if st.button("➕ Tambah Loss Event ke Tabel"):
        df = st.session_state[f"copy_{NAMA_TABEL}"]
        df = pd.concat([df, pd.DataFrame([temp.copy()])], ignore_index=True)
        st.session_state[f"copy_{NAMA_TABEL}"] = df
        st.session_state[f"temp_{NAMA_TABEL}"] = {}
        st.session_state[f"update_{NAMA_TABEL}"] = True
        df.to_excel(RECORD_FILE, index=False)
        st.success("✅ Data berhasil ditambahkan dan disimpan.")

# ======================= (C) DATA EDITOR =======================
def editor_loss_event():
    df = st.session_state[f"copy_{NAMA_TABEL}"]
    if not df.empty:
        st.markdown("### 📋 Tabel Rekap Kejadian")
        edited_df = st.data_editor(df, key="editor_loss_event", num_rows="dynamic", use_container_width=True)
        st.session_state[f"copy_{NAMA_TABEL}"] = edited_df

# ======================= (S) SIMPAN MANUAL =======================
def simpan_loss_event():
    if st.button("💾 Simpan Manual"):
        df = st.session_state[f"copy_{NAMA_TABEL}"]
        df.to_excel(RECORD_FILE, index=False)
        st.success(f"✅ Data disimpan ke: {RECORD_FILE}")

# ======================= MAIN =======================
def main():
    st.title("📊 Loss Event Reporting System")

    init_loss_event()
    load_file_loss_event()

    with st.expander("📝 Form Input Kejadian", expanded=True):
        form_loss_event()

    with st.expander("📊 Tabel Kejadian"):
        editor_loss_event()

    simpan_loss_event()

# ======================= RUN =======================
if __name__ == "__main__":
    main()
