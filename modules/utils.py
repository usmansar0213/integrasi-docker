# utils.py

import os
from datetime import datetime
import streamlit as st

def get_user_folder():
    """
    Mengembalikan path folder pengguna berdasarkan session_state['current_user'].
    Jika belum ada, folder akan otomatis dibuat.
    """
    username = st.session_state.get("current_user", "anonymous")
    folder = os.path.join("saved", username)
    os.makedirs(folder, exist_ok=True)
    return folder

def get_user_file(filename: str, subfolder: str = ""):
    """
    Menghasilkan path lengkap untuk menyimpan file ke dalam folder pengguna,
    dengan opsi subfolder tambahan.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_folder = get_user_folder()

    if subfolder:
        full_folder = os.path.join(base_folder, subfolder)
        os.makedirs(full_folder, exist_ok=True)
    else:
        full_folder = base_folder

    return os.path.join(full_folder, f"{timestamp}_{filename}")
