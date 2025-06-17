import os
import streamlit as st
import pandas as pd
from datetime import datetime
import openai
import json
import re
from io import StringIO
from bs4 import BeautifulSoup
import time
import io
# Konstanta Label
BTN_SAVE_LABEL = "💾 Simpan Data ke Excel"
BTN_GET_AI_LABEL = "🤖 Dapatkan Saran AI"
BTN_LOAD_LABEL = "📂 Muat Data dari File"

# Inisialisasi API Key OpenAI
openai.api_key = st.secrets["openai_api_key"]

# Folder tempat file disimpan
from modules.utils import get_user_file


# 🛠️ **Fungsi Inisialisasi Data Session** 🛠️
def initiate_data():
    """ Inisialisasi session state tanpa menimpa data yang sudah ada """
    keys = [
        "copy_metrix_strategi_risiko",
        "copy_Informasi Perusahaan",
        "copy_ambang_batas_risiko",
        "copy_sasaran_strategi_bisnis"
    ]

    for key in keys:
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame()
        elif isinstance(st.session_state[key], dict):  # Jika dictionary, ubah ke DataFrame
            st.session_state[key] = pd.DataFrame(st.session_state[key])
def tampilkan_tabel_dengan_nomor(df: pd.DataFrame, editable=False, key=None):
    """Menambahkan kolom 'No' dari 1 dan menampilkan tabel dengan index disembunyikan"""
    if df is None or df.empty:
        return st.write("Data tidak tersedia.")
    
    df_display = df.copy()
    
    # Tambahkan kolom "No" hanya jika belum ada
    if "No" not in df_display.columns:
        df_display.insert(0, "No", range(1, len(df_display) + 1))
    else:
        # Update isinya kalau sudah ada, untuk menjaga urutan tetap akurat
        df_display["No"] = range(1, len(df_display) + 1)

    if editable:
        return st.data_editor(
            df_display,
            hide_index=True,
            use_container_width=True,
            key=key,
            num_rows="dynamic"
        )
    else:
        return st.dataframe(
            df_display,
            hide_index=True,
            use_container_width=True
        )


# Folder tempat file disimpan
from modules.utils import get_user_file
def save_and_download_sasaran_strategi(daftar_tabel, module_name="sasaran_strategi_bisnis"):
    """
    Menyimpan data ke server dan menyediakan file untuk diunduh, dipicu oleh satu tombol.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    folder_path = "C:/saved"  # Sesuaikan jika di Docker, bisa: os.path.join(os.getcwd(), "saved")
    os.makedirs(folder_path, exist_ok=True)

    server_file_path = os.path.join(folder_path, f"{module_name}_{timestamp}.xlsx")
    output = io.BytesIO()

    # Simpan ke dua tujuan: server dan buffer untuk unduh
    with pd.ExcelWriter(server_file_path, engine='xlsxwriter') as writer_server, \
         pd.ExcelWriter(output, engine='xlsxwriter') as writer_download:

        for tabel in daftar_tabel:
            df_to_save = st.session_state.get(f"copy_{tabel}", pd.DataFrame()).copy()
            if not df_to_save.empty:
                if "No" in df_to_save.columns:
                    df_to_save.drop(columns=["No"], inplace=True)

                sheet_name = tabel[:31]
                df_to_save.to_excel(writer_server, sheet_name=sheet_name, index=False)
                df_to_save.to_excel(writer_download, sheet_name=sheet_name, index=False)

    output.seek(0)

    st.success(f"✅ Data berhasil disimpan ke server: `{server_file_path}`")

    # Tampilkan tombol download secara langsung (otomatis)
    st.download_button(
        label="⬇️ Unduh File Excel",
        data=output,
        file_name=f"{module_name}_{timestamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def load_all_data_from_file(file):
    """Muat semua sheet dari file Excel ke session_state, termasuk auto load jika file khusus (contoh: sasaran_strategi_bisnis)."""
    if file is not None:
        try:
            xls = pd.ExcelFile(file)
            for sheet_name in xls.sheet_names:
                cleaned_sheet_name = sheet_name.replace('Copy ', '').strip()
                normalized_sheet_name = cleaned_sheet_name.lower().replace(' ', '_')
                key_session = f"copy_{normalized_sheet_name}"

                df = pd.read_excel(xls, sheet_name=sheet_name)

                # Simpan ke session_state
                st.session_state[key_session] = df

            # 🔥 Tambahan: Kalau nama file mengandung "sasaran_strategi_bisnis", auto load hasil rekomendasi
            filename_lower = file.name.lower()
            if "sasaran_strategi_bisnis" in filename_lower:
                if "copy_sasaran_strategi_bisnis" in st.session_state:
                    st.session_state["temp_sasaran_strategi_bisnis"] = st.session_state["copy_sasaran_strategi_bisnis"].copy()
                    st.session_state["sasaran_strategi_bisnis"] = st.session_state["copy_sasaran_strategi_bisnis"].copy()

        except Exception as e:
            st.error(f"❌ Gagal memuat file: {e}")
    else:
        st.error("❌ Tidak ada file dipilih.")




def load_data_from_file(file):
    """Memuat data dari file yang diunggah dan menyimpannya ke session state dengan key 'copy_sasaran_strategi_bisnis'."""
    try:
        if file is not None:
            if file.name.endswith('.xlsx'):
                df = pd.read_excel(file, engine='openpyxl')
            elif file.name.endswith('.csv'):
                df = pd.read_csv(file, encoding="utf-8")
            else:
                st.error("❌ Format file tidak didukung. Harus CSV atau Excel.")
                return None

            # Simpan data langsung ke session state dengan key 'copy_sasaran_strategi_bisnis'
            st.session_state["copy_sasaran_strategi_bisnis"] = df  
            st.success(f"✅ Data berhasil dimuat dari: {file.name}")
            return df
        else:
            st.error("❌ Tidak ada file yang dipilih.")
            return None
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan saat memuat file: {e}")
        return None

def get_reference_data():
    """ Mengambil referensi data dari session state """
    metrix_risk = st.session_state.get("copy_metrix_strategi_risiko", pd.DataFrame())
    limit_risk = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame())
    profile_company = st.session_state.get("copy_Informasi Perusahaan", pd.DataFrame())

    if metrix_risk.empty or limit_risk.empty or profile_company.empty:
        st.error("❌ Data tidak lengkap. Pastikan semua dataset telah dimuat.")
        return pd.DataFrame()

    reference_data = pd.DataFrame()  # Awal kosong
    for _, row in reference_data.iterrows():
        kode_risiko = row.get("Kode Risiko", "Tidak tersedia")  # Ambil Kode Risiko dari referensi
        risk_appetite = row["Risk Appetite Statement"]
        risk_attitude = row["Sikap Terhadap Risiko"]
        limit_risk_value = row["Limit Risiko"]

        response = get_gpt_response(prompt)

        if response:
            df_recommendation = convert_gpt_response_to_dataframe(response, risk_appetite, kode_risiko)

        kode_risiko = "Tidak tersedia"
        if "Kode Risiko" in metrix_risk.columns:
            matched_risks = metrix_risk.loc[metrix_risk["Risk Appetite Statement"].str.strip() == risk_appetite, "Kode Risiko"]
            if not matched_risks.empty:
                kode_risiko = matched_risks.values[0]

        reference_row = {
            "Jenis Bisnis": profile_company.get("Jenis Bisnis", "Tidak tersedia"),
            "Risk Appetite Statement": risk_appetite,
            "Sikap Terhadap Risiko": risk_attitude,
            "Limit Risiko": limit_risk.get("Limit Risiko", "Tidak tersedia"),
            "Kode Risiko": kode_risiko
        }
        reference_data.append(reference_row)

    return pd.DataFrame(reference_data)

def request_risk_strategy_recommendations():
    all_recommendations = []

    metrix_df = st.session_state.get("copy_metrix_strategi_risiko", pd.DataFrame())
    limit_df = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame())
    profile_df = st.session_state.get("copy_Informasi Perusahaan", pd.DataFrame())

    if metrix_df.empty or limit_df.empty or profile_df.empty:
        st.error("❌ Data referensi belum lengkap.")
        return

    business_type = profile_df.iloc[0].get("Jenis Bisnis", "Tidak tersedia") if not profile_df.empty else "Tidak tersedia"
    limit_risk_value = limit_df.iloc[0].get("Limit Risiko", 0) if not limit_df.empty else 0

    for _, row in metrix_df.iterrows():
        risk_appetite = row.get("Risk Appetite Statement", "")
        risk_attitude = row.get("Sikap Terhadap Risiko", "")
        kode_risiko = row.get("Kode Risiko", "Tidak tersedia")

        risk_multiplier = {
            "Tidak Toleran": 0.0,
            "Konservatif": 0.1,
            "Moderat": 0.15,
            "Strategis": 0.2
        }

        expected_result_multiplier = {
            "Tidak Toleran": 0.01,
            "Konservatif": 0.05,
            "Moderat": 0.15,
            "Strategis": 0.2
        }

        nilai_risiko = risk_multiplier.get(risk_attitude, 0) * limit_risk_value
        hasil_diharapkan = expected_result_multiplier.get(risk_attitude, 0) * limit_risk_value

        prompt = f"""
        Anda adalah asisten manajemen risiko. Berdasarkan data berikut, berikan rekomendasi strategi:
        **Kode Risiko**: {kode_risiko}
        **Risk Appetite Statement**: "{risk_appetite}"
        
        **📌 Informasi Perusahaan**
        - **Jenis Bisnis**: {business_type}
        - **Kode Risiko**: {kode_risiko}

        **📌 Risk Appetite & Sikap Risiko**
        - **Risk Appetite Statement**: "{risk_appetite}"
        - **Sikap Terhadap Risiko**: "{risk_attitude}"

        **📌 Ambang Batas Risiko**
        - **Limit Risiko**: "{limit_risk_value}"

        **📌 Nilai Risiko yang Akan Timbul**
        - **Nilai Risiko**: "{nilai_risiko}"

        **📌 Hasil Diharapkan**
        - **Hasil Diharapkan**: "{hasil_diharapkan}"

        ---
        🎯 **Tugas Anda**:  
        Berikan rekomendasi strategi yang sesuai dengan risk appetite statement, sikap risiko, dan batas risiko.
        
        📌 **Format Output (JSON)**:
        [
            {{
                "Kode Risiko": "{kode_risiko}",
                "Pilihan Sasaran": "...",
                "Pilihan Strategi": "...",
                "Hasil Diharapkan": "{hasil_diharapkan}",
                "Nilai Risiko": "{nilai_risiko}",
                "Limit Risiko Sesuai Parameter": "{limit_risk_value}",
                "Keputusan Penetapan": "..."
            }}
        ]
        """

        response = get_gpt_response(prompt)
        if response:
            df_recommendation = convert_gpt_response_to_dataframe(response, risk_appetite, kode_risiko)
            all_recommendations = pd.concat([all_recommendations, df_recommendation], ignore_index=True)

    if not all_recommendations.empty:
        st.session_state["sasaran_strategi_bisnis"] = all_recommendations.copy()
        st.session_state["copy_sasaran_strategi_bisnis"] = all_recommendations.copy()
        st.session_state["temp_sasaran_strategi_bisnis"] = all_recommendations.copy()
        st.success("✅ Rekomendasi strategi berhasil diperoleh dari GPT.")


def get_gpt_response(prompt, system_message="Anda adalah asisten manajemen risiko.", temperature=0.7, max_tokens=2000):
    progress_bar = st.progress(0)  # Inisialisasi progress bar

    try:
        progress_bar.progress(25)  # Update progress
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        progress_bar.progress(75)
        result = response.choices[0].message.content.strip()

        progress_bar.progress(100)
        time.sleep(0.5)
        progress_bar.empty()

        return result

    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ Terjadi kesalahan saat memanggil GPT: {e}")
        return None

def extract_json_from_response(response_text):
    try:
        json_pattern = re.compile(r'\[.*?\]', re.DOTALL)
        json_match = json_pattern.search(response_text)
        if json_match:
            json_data = json_match.group()
            return json.loads(json_data)
        else:
            return None
    except json.JSONDecodeError as e:
        st.error(f"❌ Error parsing JSON: {e}")
        return None


def convert_gpt_response_to_dataframe(response_text, risk_appetite_statement, kode_risiko):
    
    extracted_json = extract_json_from_response(response_text)
    if extracted_json:
        columns = [
            "Kode Risiko",
            "Risk Appetite Statement",
            "Pilihan Sasaran",
            "Pilihan Strategi",
            "Hasil Diharapkan",
            "Nilai Risiko",
            "Limit Risiko Sesuai Parameter",
            "Keputusan Penetapan"
        ]
        df = pd.DataFrame(extracted_json, columns=columns)
        df["Risk Appetite Statement"] = risk_appetite_statement
        df["Kode Risiko"] = kode_risiko if kode_risiko else "Tidak tersedia"
        return df
    else:
        st.error("❌ Gagal mengonversi respons AI ke dalam format tabel. Pastikan respons dalam format JSON yang valid.")
        return pd.DataFrame()


def string_to_dataframe(data_str):
    try:
        return pd.read_csv(StringIO(data_str))
    except Exception:
        try:
            return pd.read_json(StringIO(data_str))
        except Exception:
            st.error("❌ Gagal mengonversi string ke DataFrame.")
            return pd.DataFrame()


def convert_dataframe_to_html(df):
    if df is not None and not df.empty:
        return df.to_html(classes='table table-striped', index=False, border=0)
    else:
        return "<p>Tidak ada data untuk ditampilkan.</p>"


def html_to_dataframe(html_data):
    try:
        soup = BeautifulSoup(html_data, "html.parser")
        table = soup.find("table")
        df = pd.read_html(str(table))[0]
        return df
    except Exception as e:
        st.error(f"❌ Gagal mengonversi HTML ke DataFrame: {e}")
        return pd.DataFrame()

def main():
    st.title("📊 Sasaran Strategi Bisnis")

    # Tombol Muat Data dari File
    uploaded_file = st.file_uploader("📥 Silahkan Load file Profil Perusahaan", type=["xls", "xlsx"], key="data_uploader")
    if uploaded_file is not None:
        load_all_data_from_file(uploaded_file)


    # Inisialisasi LETACS key
    initiate_data()
    if "copy_sasaran_strategi_bisnis" not in st.session_state:
        st.session_state["copy_sasaran_strategi_bisnis"] = pd.DataFrame()
    if "temp_sasaran_strategi_bisnis" not in st.session_state:
        st.session_state["temp_sasaran_strategi_bisnis"] = st.session_state["copy_sasaran_strategi_bisnis"].copy()
    if "sasaran_strategi_bisnis" not in st.session_state:
        st.session_state["sasaran_strategi_bisnis"] = pd.DataFrame()

    # Expander referensi
    with st.expander("📋 **Data Risiko & Strategi**", expanded=False):
        st.subheader("📊 Copy Metrix Strategi Risiko")
        tampilkan_tabel_dengan_nomor(st.session_state.get("copy_metrix_strategi_risiko", pd.DataFrame()))

        st.subheader("🏢 Profil Perusahaan - Informasi Perusahaan")
        tampilkan_tabel_dengan_nomor(st.session_state.get("copy_informasi_perusahaan", pd.DataFrame()))

        st.subheader("📉 Ambang Batas Risiko")
        tampilkan_tabel_dengan_nomor(st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame()))

    # Tombol Dapatkan Saran AI
    if st.button(BTN_GET_AI_LABEL, key="get_ai_button"):
        all_recommendations = pd.DataFrame()

        if "copy_metrix_strategi_risiko" in st.session_state:
            risk_statements = st.session_state["copy_metrix_strategi_risiko"]
            if not risk_statements.empty:
                for _, row in risk_statements.iterrows():
                    kode_risiko = row.get("Kode Risiko", "Tidak tersedia")  # ✅ Tambahkan baris ini
                    risk_appetite = row["Risk Appetite Statement"]
                    sikap_terhadap_risiko = row.get("Sikap Terhadap Risiko", "Tidak tersedia")
                    parameter = row.get("Parameter", "Tidak tersedia")
                    satuan_ukuran = row.get("Satuan Ukuran", "Tidak tersedia")
                    nilai_batasan = row.get("Nilai Batasan/Limit", "Tidak tersedia")

                    # 🔹 Prompt yang lebih dinamis dan tidak copy-paste
                    prompt = f"""Anda adalah asisten ahli dalam manajemen risiko dengan pemahaman mendalam tentang strategi bisnis. 
                    Tugas Anda adalah memberikan saran strategi berdasarkan informasi perusahaan, risk appetite, dan batasan risiko yang telah ditentukan.

                    ### **Informasi Perusahaan**
                    Berikut adalah karakteristik bisnis perusahaan yang harus Anda jadikan acuan:
                    {json.dumps(st.session_state.get("copy_Informasi Perusahaan", {}).to_dict(), indent=2)}

                    ### **Batasan Risiko**
                    Berikut adalah limit risiko yang harus diperhatikan dalam strategi yang Anda berikan:
                    {json.dumps(st.session_state.get("copy_ambang_batas_risiko", {}).to_dict(), indent=2)}

                    ### **Risk Appetite & Parameter**
                    Berikut adalah informasi spesifik tentang risk appetite dan parameter yang digunakan:
                    - **Risk Appetite Statement**: "{str(risk_appetite)}"
                    - **Sikap Terhadap Risiko**: "{str(sikap_terhadap_risiko)}"
                    - **Parameter**: "{str(parameter)}"
                    - **Satuan Ukuran**: "{str(satuan_ukuran)}"
                    - **Nilai Batasan/Limit**: "{str(nilai_batasan)}"

                    ---

                    ### **Panduan dalam menjawab**
                    Berdasarkan data di atas, buat rekomendasi strategi yang selaras dengan bisnis perusahaan dan mempertimbangkan batasan risiko yang telah ditentukan.

                    1️⃣ **Pilihan Sasaran**  
                       - Sesuaikan tujuan dengan risk appetite dan selalu berikan target kuantitatif yang realistis dengan format sasaran/ angka target

                    2️⃣ **Pilihan Strategi**  
                       - Berikan strategi inovatif yang dapat dicapai berdasarkan dengan risk appetite dan bisnis perusahaan 

                    3️⃣ **Hasil yang Diharapkan**  
                       - Angka tanpa penjelasan, misal Rp.50 (Juta) yaitu nilai rupiah yang diharapkan diperoleh perusahaan jika strategi berjalan dengan baik. Tanpa teks tambahan.

                    4️⃣ **Nilai Risiko yang Akan Timbul**  
                       - Angka tanpa penjelasan, misal Rp.50 (Juta), yaitu nilai rupiah yang akan timbul akibat menjalankan strategi.
                       - Sesuaikan dengan industri dan nilai parameter yang diberikan.
                       - Tanpa teks tambahan.

                    5️⃣ **Nilai Limit Risiko**  
                       - Angka tanpa penjelasan, misal Rp.50 (Juta), yaitu nilai rupiah yang sesuai dengan nilai limit risiko sesuai parameter risiko dalam metrik strategi risiko. Tanpa teks tambahan.

                    6️⃣ **Keputusan Penetapan**  
                       - **Lanjut**, apabila imbal hasil (return) yang akan diperoleh sebanding dengan risiko yang dapat diterima oleh perusahaan.

                    **Output harus berupa array JSON dengan format berikut**:
                    [
                        {{
                            "Kode Risiko": "{kode_risiko}",
                            "Pilihan Sasaran": "...",
                            "Pilihan Strategi": "...",
                            "Hasil Diharapkan": "...",
                            "Nilai Risiko": "...",
                            "Limit Risiko Sesuai Parameter": "...",
                            "Keputusan Penetapan": "..."
                        }}
                    ]
                    """

                                  
                    response = get_gpt_response(prompt)
                    if response:
                        kode_risiko = row.get("Kode Risiko", "Tidak tersedia")
                        df_recommendation = convert_gpt_response_to_dataframe(response, risk_appetite, kode_risiko)
                        all_recommendations = pd.concat([all_recommendations, df_recommendation], ignore_index=True)

                if not all_recommendations.empty:
                    st.session_state["sasaran_strategi_bisnis"] = all_recommendations.copy()  # hasil asli dari GPT
                    st.session_state["copy_sasaran_strategi_bisnis"] = all_recommendations.copy()
                    st.session_state["temp_sasaran_strategi_bisnis"] = all_recommendations.copy()
                    st.success("✅ Rekomendasi strategi berhasil dimuat dari GPT.")

    # Editor interaktif (T)
    st.subheader("📝 Edit Sasaran Strategi Bisnis")
    temp_df = tampilkan_tabel_dengan_nomor(
        st.session_state["temp_sasaran_strategi_bisnis"],
        editable=True,
        key="data_editor"
    )
    st.session_state["temp_sasaran_strategi_bisnis"] = temp_df

    # Tombol Apply (A)
    if st.button("🔄 Update Data"):
        st.session_state["copy_sasaran_strategi_bisnis"] = st.session_state["temp_sasaran_strategi_bisnis"].copy()
        st.success("✅ Hasil edit berhasil disimpan ke copy_sasaran_strategi_bisnis.")

    # Tombol Simpan dan Unduh (gabungan)
    if st.button("💾 Simpan & ⬇️ Unduh Excel", key="save_and_download"):
        daftar_tabel = ["sasaran_strategi_bisnis"]
        save_and_download_sasaran_strategi(daftar_tabel, module_name="sasaran_strategi_bisnis")



if __name__ == '__main__':
    main()
