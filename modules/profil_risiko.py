import streamlit as st
import pandas as pd
import openai
import time
import json
import os
import re
from datetime import datetime
from modules.utils import get_user_file
import io


def get_user_file(filename: str):
    username = st.session_state.get("current_user", "anonymous")
    folder = os.path.join("saved", username)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, filename)

# Inisialisasi session state secara langsung
if "copy_deskripsi_risiko" not in st.session_state:
    st.session_state.update({
        "copy_deskripsi_risiko": pd.DataFrame(),
        "copy_kri": pd.DataFrame(),
        "copy_control_dampak": pd.DataFrame(),
        "selected_risks": {},
        "gpt_risks": {},
        "risk_details": {},
         "copy_risk_details": {},
        "copy_sasaran_strategi_bisnis": pd.DataFrame(),
        "copy_opsi_risiko": {},  # ✅ Inisialisasi yang sebelumnya error
        "copy_selected_risk": pd.DataFrame()
    })
if (
    "copy_sasaran_strategi_bisnis" not in st.session_state
    or not isinstance(st.session_state["copy_sasaran_strategi_bisnis"], pd.DataFrame)
    or st.session_state["copy_sasaran_strategi_bisnis"].empty
):
    st.session_state["copy_sasaran_strategi_bisnis"] = pd.DataFrame()

def init_session_state():
    default_keys = {
        "copy_deskripsi_risiko": pd.DataFrame(),
        "copy_key_risk_indicator": pd.DataFrame(),  # ✅ Ganti dari copy_kri
        "copy_control_dampak": pd.DataFrame(),
        "selected_risks": {},                       # ✅ Untuk simpan checkbox
        "gpt_risks": {},                             # ✅ Kalau ada output GPT lain
        "risk_details": {},                          # ✅ Versi dict hasil GPT
        "copy_risk_details": pd.DataFrame(),         # ✅ Versi DataFrame hasil GPT
        "copy_update_risk_details": pd.DataFrame(),  # ✅ Setelah diedit di editor
        "copy_sasaran_strategi_bisnis": pd.DataFrame(),  # ✅ Untuk strategi awal
        "copy_opsi_risiko": {},                      # ✅ Opsi risiko hasil GPT
        "copy_selected_risk": pd.DataFrame(),        # ✅ Risiko yang dipilih user
        "final_risk_profile": pd.DataFrame()         # ✅ Data akhir untuk ekspor
    }

    for key, default_value in default_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    
# Fungsi untuk mengambil data dari session state
def get_data_from_session():
    return st.session_state["copy_sasaran_strategi_bisnis"]

# Fungsi untuk menampilkan tabel data
def display_table(data):
    if data.empty:
        st.warning("Tidak ada data yang tersedia dalam session state.")
    else:
        st.dataframe(data, hide_index=True)

# Fungsi untuk mendapatkan opsi risiko dari OpenAI GPT
def get_risk_options(kode_risiko, pilihan_strategi):
    prompt = (f"Untuk strategi '{pilihan_strategi}' dengan kode risiko '{kode_risiko}', "
              "beri saya 3 opsi risiko yang mungkin terjadi dalam format berikut:\n"
              "Peristiwa Risiko\n"
              f"Kode Risiko: {kode_risiko}\n"
              f"Pilihan Strategi: {pilihan_strategi}\n"
              "1. Risiko pertama\n"
              "2. Risiko kedua\n"
              "3. Risiko ketiga")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Anda adalah asisten yang membantu dalam analisis risiko."},
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response["choices"][0]["message"]["content"].split("\n")
    risk_list = [line.split(". ", 1)[1] for line in response_text if line.startswith(("1", "2", "3"))]
    return risk_list

def normalize_dampak_anggaran(value):
    """Normalisasi nilai kolom Dampak Anggaran agar hanya 'Biaya' atau 'Pendapatan'."""
    if isinstance(value, str):
        value = value.lower()
        if "biaya" in value:
            return "Biaya"
        elif "pendapatan" in value:
            return "Pendapatan"
    return ""

# Fungsi untuk membuat opsi risiko dan menyimpannya dalam session state
def generate_risk_options(data):
    total_rows = len(data)
    if total_rows == 0:
        st.warning("Tidak ada data untuk diproses.")
        return
    
    progress_bar = st.progress(0)

    for idx, (_, row) in enumerate(data.iterrows()):
        kode_risiko = row["Kode Risiko"]
        pilihan_strategi = row["Pilihan Strategi"]

        identifier = f"{kode_risiko} | {pilihan_strategi}"
        # Selalu update hasil dari GPT (bisa diulang)
        opsi_risiko = get_risk_options(kode_risiko, pilihan_strategi)
        st.session_state["copy_opsi_risiko"][identifier] = {
            "kode_risiko": kode_risiko,
            "pilihan_strategi": pilihan_strategi,
            "opsi_risiko": opsi_risiko
        }

        progress_bar.progress((idx + 1) / total_rows)
    
    progress_bar.empty()
    st.success("Peristiwa risiko berhasil dihasilkan!")

# Fungsi untuk menampilkan opsi risiko dalam bentuk checkbox
def display_risk_options():
    """Menampilkan opsi risiko dalam bentuk checkbox dan menyimpan pilihan dalam session state."""
    st.session_state.setdefault("copy_opsi_risiko", {})
    st.session_state.setdefault("selected_risks", {})
    st.session_state.setdefault("copy_selected_risk", pd.DataFrame())

    if not st.session_state["copy_opsi_risiko"]:
        st.warning("Belum ada opsi risiko yang dihasilkan.")
        return pd.DataFrame()

    opsi_risiko_list = []

    for identifier, data in st.session_state["copy_opsi_risiko"].items():
        kode_risiko = data.get("kode_risiko", identifier.split(" | ")[0])
        pilihan_strategi = data.get("pilihan_strategi", identifier.split(" | ")[1])
        opsi_risiko = data.get("opsi_risiko", [])

        st.write(f"**Kode Risiko: {kode_risiko}** | **Strategi: {pilihan_strategi}**")

        for opsi in opsi_risiko:
            checkbox_key = f"{identifier}_{opsi}"
            checked = st.checkbox(
                opsi,
                key=f"checkbox_{checkbox_key}",
                value=st.session_state["selected_risks"].get(checkbox_key, False)
            )

            st.session_state["selected_risks"][checkbox_key] = checked

            if checked:
                opsi_risiko_list.append({
                    "Kode Risiko": kode_risiko,
                    "Pilihan Strategi": pilihan_strategi,
                    "Peristiwa Risiko": opsi
                })

    df_selected = pd.DataFrame(opsi_risiko_list)
    st.session_state["copy_selected_risk"] = df_selected

    return df_selected

def get_risk_details_from_gpt():
    selected_df = st.session_state.get("copy_selected_risk", pd.DataFrame())
    
    if selected_df is None or selected_df.empty:
        st.warning("Tidak ada risiko yang dipilih untuk diminta saran detail.")
        return pd.DataFrame()

    hasil_saran = []
    st.subheader("Hasil Saran Detail Risiko dari GPT")
    total = len(selected_df)
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, row in selected_df.iterrows():
        kode_risiko = row.get("Kode Risiko", "-")
        strategi = row.get("Pilihan Strategi", "-")
        opsi = row.get("Peristiwa Risiko", "-")

        prompt = f"""
        Beri saya saran detail risiko dalam format JSON berikut:
        {{
            "Kode Risiko": "{kode_risiko}",
            "Peristiwa Risiko": "{opsi}",
            "Deskripsi Peristiwa Risiko": "Penjelasan lebih detail mengenai '{opsi}' dalam konteks risiko",
            "No. Penyebab Risiko": "1",
            "Kode Penyebab Risiko": "PTPI-1",
            "Penyebab Risiko": "Penyebab dari aspek people, process, network, system",
            "Key Risk Indicators (KRI)": "Indikator early warning tanda risiko akan terjadi",
            "Unit KRI": "Amount/Percentage/Range/Kualitatif",
            "KRI Aman": "Nilai yang menunjukkan situasi aman",
            "KRI Hati-Hati": "Nilai yang menunjukkan situasi hati-hati",
            "KRI Bahaya": "Nilai yang menunjukkan situasi bahaya",
            "Jenis Existing Control": "Pilih salah satu dari: 'Kontrol Operasi', 'Kontrol Kepatuhan', 'Kontrol Pelaporan'",
            "Existing Control": "Penjelasan mengenai kontrol yang ada",
            "Penilaian Efektivitas Kontrol": "Pilih salah satu dari: 'Cukup dan Efektif', 'Cukup dan Efektif Sebagian', 'Cukup dan Tidak Efektif', 'Tidak Cukup dan Efektif Sebagian', 'Tidak Cukup dan Tidak Efektif'",
            "Kategori Dampak": "Kuantitatif atau Kualitatif",
            "Deskripsi Dampak": "Penjelasan dampak dari risiko",
            "Perkiraan Waktu Terpapar Risiko": "Estimasi waktu terpapar",
            "Dampak Anggaran": "Apakah risiko berdampak pada 'Pendapatan' atau 'Biaya'? Pilih salah satu."
        }}
        """

        with st.spinner(f"Meminta saran dari GPT untuk risiko: {kode_risiko} - {opsi}"):
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Anda adalah asisten manajemen risiko yang sangat teliti."},
                    {"role": "user", "content": prompt}
                ]
            )

            raw_output = response["choices"][0]["message"]["content"]

            try:
                raw_output_cleaned = re.sub(r"```(json)?", "", raw_output).strip()
                parsed_json = json.loads(raw_output_cleaned)

                # Tambahkan identifier unik
                identifier = f"{kode_risiko} | {opsi}"
                parsed_json["identifier"] = identifier

                hasil_saran.append(parsed_json)

            except json.JSONDecodeError as e:
                st.error(f"❌ Gagal parsing JSON untuk {kode_risiko}: {e}")
                st.text("Raw Text dari GPT yang tidak bisa diparse:")
                st.code(raw_output, language="json")

        # Update progress
        progress_bar.progress((i + 1) / total)
        status_text.text(f"Memproses {i + 1} dari {total} risiko...")

    progress_bar.empty()
    status_text.text("✅ Semua risiko telah diproses.")

    # ✅ Konversi hasil saran ke DataFrame
    df_hasil = pd.DataFrame(hasil_saran)

    # ❗ Simpan versi dict ke risk_details (jika dibutuhkan untuk key-based access)
    risk_dict = {row["identifier"]: row for _, row in df_hasil.iterrows()}
    st.session_state["risk_details"] = risk_dict

    # ✅ Simpan versi DataFrame ke copy_risk_details (yang digunakan untuk editor dll)
    st.session_state["copy_risk_details"] = df_hasil

    return df_hasil

    
def extract_numbers_and_symbols(text):
    """Ekstrak hanya angka dan simbol dari teks."""
    if isinstance(text, str):
        return "".join(re.findall(r'[\d.,%+-]+', text))
    return text  # Jika bukan string, kembalikan nilai asli

def parse_gpt_output(text):
    if isinstance(text, pd.DataFrame):
        if "Detail Saran" in text.columns:
            text = "\n\n".join(text["Detail Saran"].astype(str).tolist())
        else:
            st.warning("Input sudah berbentuk DataFrame lengkap, tidak perlu parsing lagi.")
            st.session_state["copy_risk_details"] = text
            return text
        if "Dampak Anggaran" in df.columns:
            df["Dampak Anggaran"] = df["Dampak Anggaran"].apply(
                lambda x: x if x in ["Pendapatan", "Biaya"] else ""
            )


    if not isinstance(text, str):
        raise TypeError("Data yang diberikan ke parse_gpt_output bukan string.")

    try:
        text = re.sub(r"```(json)?", "", text).strip()
        data = json.loads(text)
        
        # Jika berupa dict, ubah ke DataFrame
        df = pd.DataFrame([data]) if isinstance(data, dict) else pd.DataFrame(data)
        # Normalisasi nilai kolom "Dampak Anggaran"
        if "Dampak Anggaran" in df.columns:
            df["Dampak Anggaran"] = df["Dampak Anggaran"].apply(normalize_dampak_anggaran)
        
        # Parsing khusus untuk KRI agar hanya menyimpan angka dan simbol
        kri_cols = ["KRI Aman", "KRI Hati-Hati", "KRI Bahaya"]
        for col in kri_cols:
            if col in df.columns:
                df[col] = df[col].apply(extract_numbers_and_symbols)

    except json.JSONDecodeError as e:
        st.error(f"Parsing JSON gagal: {e}")
        return pd.DataFrame()

    all_rows = list(st.session_state["risk_details"].values())
    df = pd.DataFrame(all_rows)
    # Normalisasi kolom "Dampak Anggaran"
    if "Dampak Anggaran" in df_hasil.columns:
        df_hasil["Dampak Anggaran"] = df_hasil["Dampak Anggaran"].apply(normalize_dampak_anggaran)

    return df
    
def split_copy_risk_details():
    """Memisahkan data dari copy_update_risk_details menjadi 3 tabel utama: Deskripsi Risiko, KRI, dan Control & Dampak."""

    if (
        "copy_update_risk_details" not in st.session_state or 
        not isinstance(st.session_state["copy_update_risk_details"], pd.DataFrame) or 
        st.session_state["copy_update_risk_details"].empty
    ):
        st.warning("❌ Data copy_update_risk_details tidak ditemukan atau kosong.")
        return

    df = st.session_state["copy_update_risk_details"].copy()

    if "Kode Risiko" not in df.columns:
        st.error("⚠️ Kode Risiko tidak ditemukan di copy_update_risk_details! Periksa hasil parsing JSON.")
        return

    # 1️⃣ Tabel Deskripsi Risiko
    deskripsi_risiko_cols = [
        "Kode Risiko", "Peristiwa Risiko", "Deskripsi Peristiwa Risiko",
        "No. Penyebab Risiko", "Kode Penyebab Risiko", "Penyebab Risiko"
    ]
    deskripsi_risiko = df.filter(items=deskripsi_risiko_cols, axis=1).fillna("")
    deskripsi_risiko = deskripsi_risiko.reset_index(drop=True)
    deskripsi_risiko.insert(0, "No", deskripsi_risiko.index + 1)

    # 2️⃣ Tabel KRI
    kri_cols = [
        "Kode Risiko", "Peristiwa Risiko", "Key Risk Indicators (KRI)",
        "Unit KRI", "KRI Aman", "KRI Hati-Hati", "KRI Bahaya"
    ]
    
    key_risk_indicator = df.filter(items=kri_cols, axis=1).fillna("")
    key_risk_indicator = key_risk_indicator.reset_index(drop=True)
    key_risk_indicator.insert(0, "No", key_risk_indicator.index + 1)

    # 3️⃣ Tabel Control & Dampak
    control_dampak_cols = [
        "Kode Risiko", "Jenis Existing Control",
        "Existing Control", "Penilaian Efektivitas Kontrol",
        "Kategori Dampak", "Deskripsi Dampak", "Perkiraan Waktu Terpapar Risiko", "Dampak Anggaran"
    ]
    control_dampak = df.filter(items=control_dampak_cols, axis=1).fillna("")
    control_dampak = control_dampak.reset_index(drop=True)
    control_dampak.insert(0, "No", control_dampak.index + 1)

    # Simpan hasil split ke session state
    st.session_state["copy_deskripsi_risiko"] = deskripsi_risiko
    st.session_state["copy_key_risk_indicator"] = key_risk_indicator
    st.session_state["copy_control_dampak"] = control_dampak

def save_and_download_profil_risiko(daftar_tabel, kode_perusahaan):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Cek dan buat folder C:/saved
    folder_path = "C:/saved"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Path untuk simpan server
    server_file_path = os.path.join(folder_path, f"Profil_Risiko_{kode_perusahaan}_{timestamp}.xlsx")

    # Buat file Excel dua kali: satu untuk server, satu untuk download
    output = io.BytesIO()
    with pd.ExcelWriter(server_file_path, engine='xlsxwriter') as writer_server, \
         pd.ExcelWriter(output, engine='xlsxwriter') as writer_download:
        
        df_kode = pd.DataFrame([[kode_perusahaan]], columns=["Kode Perusahaan"])
        df_kode.to_excel(writer_server, sheet_name="Kode Perusahaan", index=False)
        df_kode.to_excel(writer_download, sheet_name="Kode Perusahaan", index=False)

        for tabel in daftar_tabel:
            df_to_save = st.session_state.get(f"copy_{tabel}", pd.DataFrame())
            if isinstance(df_to_save, pd.DataFrame) and not df_to_save.empty:
                sheet_name = tabel[:31]
                df_to_save.to_excel(writer_server, sheet_name=sheet_name, index=False)
                df_to_save.to_excel(writer_download, sheet_name=sheet_name, index=False)

    output.seek(0)

    # ⬇️ Tombol download
    st.download_button(
        label="⬇️ Unduh Data Profil Risiko",
        data=output,
        file_name=f"Profil_Risiko_{kode_perusahaan}_{timestamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def load_uploaded_file_flexible(uploaded_file):
    """Muat file upload, otomatis deteksi apakah Sasaran Strategis atau Profil Risiko."""
    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names

            # Deteksi file berdasarkan sheet name
            if any("sasaran" in sheet.lower() and "strategi" in sheet.lower() for sheet in sheet_names):
                # File Sasaran Strategis
                matched_sheet = next((sheet for sheet in sheet_names if "sasaran" in sheet.lower() and "strategi" in sheet.lower()), None)
                if matched_sheet:
                    df = pd.read_excel(xls, sheet_name=matched_sheet)
                    st.session_state["copy_sasaran_strategi_bisnis"] = df
                    st.success(f"✅ File terdeteksi sebagai 'Sasaran Strategis' dan berhasil dimuat dari sheet '{matched_sheet}'.")
                else:
                    st.warning("⚠️ Sheet Sasaran Strategis tidak ditemukan di file.")

            elif "Profil Risiko" in sheet_names:
                # File Profil Risiko
                df = pd.read_excel(xls, sheet_name="Profil Risiko")

                if df.empty:
                    st.warning("⚠️ Sheet 'Profil Risiko' kosong.")
                    return

                if "identifier" not in df.columns:
                    df["identifier"] = df["Kode Risiko"] + " | " + df["Peristiwa Risiko"]

                st.session_state["copy_risk_details"] = df
                st.session_state["risk_details"] = {
                    row["identifier"]: row for _, row in df.iterrows()
                }

                st.success("✅ File terdeteksi sebagai 'Profil Risiko' dan berhasil dimuat dari sheet 'Profil Risiko'.")

            elif "update_risk_details" in sheet_names:
                # Deteksi sebagai file hasil ekspor aplikasi (Profil Risiko)
                df = pd.read_excel(xls, sheet_name="update_risk_details")

                if df.empty:
                    st.warning("⚠️ Sheet 'update_risk_details' kosong.")
                    return

                if "identifier" not in df.columns:
                    df["identifier"] = df["Kode Risiko"] + " | " + df["Peristiwa Risiko"]

                st.session_state["copy_risk_details"] = df
                st.session_state["risk_details"] = {
                    row["identifier"]: row for _, row in df.iterrows()
                }

                st.success("✅ File terdeteksi sebagai 'Profil Risiko' dari sheet 'update_risk_details' dan berhasil dimuat.")

            else:
                st.warning("⚠️ File tidak dikenali. Harap upload file Sasaran Strategis atau Profil Risiko yang sesuai.")

        except Exception as e:
            st.error(f"❌ Gagal memuat file: {e}")


def main():
    init_session_state()

    st.title("📌 Profil Risiko")

    # 🔵 Satu uploader untuk semua
    uploaded_files = st.file_uploader(
    "📥 Silakan unggah **file Strategi Risiko** (.xlsx)",
    type=["xlsx"],
    accept_multiple_files=True,
    key="file_uploader_multi")

    if uploaded_files:
        load_uploaded_file_flexible(uploaded_file)

    # 🔵 Ambil data sasaran strategi bisnis
    data = st.session_state.get("copy_sasaran_strategi_bisnis", pd.DataFrame())

    with st.expander("📋 Tabel Sasaran Strategi Bisnis"):
        display_table(data)

    # Tombol untuk generate opsi risiko
    if st.button("Generate Peristiwa Risiko"):
        generate_risk_options(data)

    # Menampilkan opsi risiko yang dipilih
    st.subheader("Risiko yang Dipilih")
    df_selected = display_risk_options()

    # Menampilkan tabel risiko yang dipilih dalam editor (editable table)
    if not df_selected.empty:
        st.subheader("Edit Risiko yang Dipilih")

        # Tambahkan kolom nomor urut
        df_selected = df_selected.reset_index(drop=True)
        df_selected.insert(0, "No", df_selected.index + 1)

        edited_df = st.data_editor(df_selected, num_rows="dynamic")

        # Tombol update untuk menyimpan data yang dipilih ke session state
        if st.button("Update Data Risiko"):
            st.session_state["copy_selected_risk"] = edited_df
            st.success("Data Risiko telah diperbarui!")

    else:
        st.warning("Tidak ada opsi risiko yang dipilih.")

    if st.button("Minta Saran Detail Risiko dari GPT"):
        raw_text = get_risk_details_from_gpt()
        if isinstance(raw_text, pd.DataFrame) and not raw_text.empty:
            hasil_df = parse_gpt_output(raw_text)
        else:
            st.warning("Data dari GPT kosong atau tidak valid.")

    # **Debugging: Cek apakah data risiko telah tersimpan di session state**
    if (
        "copy_risk_details" in st.session_state
        and isinstance(st.session_state["copy_risk_details"], pd.DataFrame)
        and not st.session_state["copy_risk_details"].empty
    ):
        st.subheader("Detail Risiko -silahkan edit disini")

        # Salin dan filter duplikat berdasarkan kombinasi unik
        df_risk_details = st.session_state["copy_risk_details"].copy()
        df_risk_details = df_risk_details.drop_duplicates(subset=["Kode Risiko", "Peristiwa Risiko"])
        df_risk_details = df_risk_details.reset_index(drop=True)
        if "No" not in df_risk_details.columns:
            df_risk_details.insert(0, "No", df_risk_details.index + 1)
        else:
            df_risk_details["No"] = df_risk_details.index + 1


        updated_df = st.data_editor(df_risk_details, num_rows="dynamic", key="risk_details_editor")

        # 🔥 Tombol Update + Split + Save + Download
        if st.button("💾 Update Data"):
            # ✅ Update session state
            st.session_state["copy_update_risk_details"] = updated_df

            # ✅ Otomatis split ke 3 tabel
            split_copy_risk_details()

            # ✅ Save ke server + Download
            daftar_tabel = ["update_risk_details", "deskripsi_risiko", "key_risk_indicator", "control_dampak"]
            kode_perusahaan = "PLND"  # Ini bisa kamu otomatis ambil kalau mau
            save_and_download_profil_risiko(daftar_tabel, kode_perusahaan)

    else:
        st.warning("📌 Belum ada data risiko untuk diedit.")
