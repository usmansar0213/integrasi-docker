import os
import streamlit as st
import pandas as pd
from datetime import datetime
import openai

# Konstanta label tombol yang seragam
BTN_SAVE_LABEL = "💾 Simpan Data ke Excel"
BTN_LOAD_LABEL = "📤 Muat Data dari Excel"
BTN_DOWNLOAD_LABEL = "⬇️ Unduh File Excel"
BTN_GET_AI_LABEL = "🤖 Dapatkan Saran AI"
BTN_UPDATE_TAXONOMY_LABEL = "🔄 Perbarui Taksonomi Risiko"

# Inisialisasi API key OpenAI dari environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def init_session(default_df, session_key="data", temp_key="temp_data"):
    """
    Inisialisasi st.session_state dengan kunci yang diberikan.
    """
    if session_key not in st.session_state:
        st.session_state[session_key] = default_df.copy()
    if temp_key not in st.session_state:
        st.session_state[temp_key] = st.session_state[session_key].copy()

def save_excel_data(data, module_name="Module", folder_path=None):
    """
    Menyimpan DataFrame atau dictionary DataFrame ke file Excel di folder yang ditentukan.
    """
    if folder_path is None:
        folder_path = os.getcwd()  # Default ke direktori kerja saat ini

    os.makedirs(folder_path, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{module_name}_{timestamp}.xlsx"
    full_path = os.path.join(folder_path, filename)
    
    if isinstance(data, dict):
        with pd.ExcelWriter(full_path, engine='openpyxl') as writer:
            for sheet_name, df in data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        data.copy().to_excel(full_path, index=False, engine='openpyxl')
        
    st.success(f"✅ Data berhasil disimpan di: `{full_path}`")
    return full_path

def load_excel_data(uploaded_file, required_columns, sheet_name=None):
    """
    Memuat data dari file Excel yang diunggah dan memvalidasi struktur kolom.
    """
    if uploaded_file is not None:
        try:
            if not uploaded_file.name.endswith((".xls", ".xlsx")):
                st.error("❌ Format file tidak didukung. Harap unggah file Excel.")
                return None
            
            # Membaca semua sheet jika sheet_name=None
            excel_data = pd.read_excel(uploaded_file, engine='openpyxl', sheet_name=sheet_name)

            # Jika sheet_name=None, ambil sheet pertama
            if isinstance(excel_data, dict):
                sheet_names = list(excel_data.keys())
                df = excel_data[sheet_names[0]]  # Ambil sheet pertama
            else:
                df = excel_data

            # Validasi kolom
            if not all(col in df.columns for col in required_columns):
                st.error("❌ Struktur kolom tidak sesuai. Harap unggah file dengan format yang benar.")
                return None

            st.success("✅ Data berhasil dimuat dari file Excel!")
            return df

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat memuat data: {e}")
            return None


def get_gpt_response(prompt, system_message="Anda adalah asisten yang membantu.", temperature=0.7, max_tokens=2000):
    """
    Mengirim prompt ke OpenAI GPT dan mengembalikan responsnya.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan saat memanggil GPT: {e}")
        return None
