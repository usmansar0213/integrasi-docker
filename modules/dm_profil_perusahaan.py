# dm_profil_perusahaan.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from main import get_user_file, get_user_folder


def init_profil_session(default_df):
    """
    Inisialisasi session state untuk 'profil_data' dan 'temp_data'
    jika belum ada.
    """
    if "profil_data" not in st.session_state:
        st.session_state.profil_data = default_df.copy()
    if "temp_data" not in st.session_state:
        st.session_state.temp_data = st.session_state.profil_data.copy()



def save_data_to_local(data):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = get_user_file(f"Profil_Perusahaan_{timestamp}.xlsx")
    data.copy().to_excel(file_path, index=False, engine='openpyxl')
    st.success(f"✅ Data berhasil disimpan di: `{file_path}`")
    return file_path


def load_data_from_local(uploaded_file):
    """
    Memuat data dari file Excel yang diunggah dan memvalidasi struktur kolom.
    """
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith((".xls", ".xlsx")):
                loaded_data = pd.read_excel(uploaded_file, engine='openpyxl')
            else:
                st.error("❌ Format file tidak didukung. Hanya file Excel yang diperbolehkan.")
                return None

            required_columns = ["modul", "sub_modul", "Item", "Input Pengguna"]
            if not all(col in loaded_data.columns for col in required_columns):
                st.error("❌ Struktur kolom tidak sesuai. Harap unggah file dengan format yang benar.")
                return None

            st.success("✅ Data berhasil dimuat dari file Excel!")
            return loaded_data
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat memuat data: {e}")
            return None
