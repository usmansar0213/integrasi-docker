# ============================ #
# 📌 IMPORT & SETUP DASAR
# ============================ #
import streamlit as st
import os
import sys
import importlib
import traceback
import openai
import pandas as pd
import yfinance as yf

# ------------------ PATH MODULE ------------------ #
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, "modules")
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

# ============================ #
# 🔧 SECTION: FUNGSI UTAMA
# ============================ #
def set_custom_page_layout():
    st.markdown(
        """
        <style>
        /* ==== AREA UTAMA ==== */
        .block-container {
            padding-top: 3.5rem !important;  /* ruang cukup untuk marquee */
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
        }

        .main {
            max-width: 100% !important;
        }

        /* ==== SIDEBAR SUPER NAIK ==== */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0rem !important;     /* posisi paling atas */
            margin-top: -1rem !important;     /* lebih ekstrim, nempel ke atas */
        }

        /* Sidebar width */
        .css-1d391kg {
            width: 250px !important;
        }

        /* Kurangi jarak antar elemen konten */
        .stMarkdown, .stDataFrame {
            margin-bottom: 0.5rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def tampilkan_running_text():
    """
    Menampilkan running text di bagian atas halaman dengan data dari Yahoo Finance.
    Jika koneksi gagal, menampilkan fallback dengan notifikasi.
    """
    with st.spinner("🔄 Mengambil data nilai tukar dan harga komoditas..."):
        data = get_ticker_data()

    if not data:
        st.warning("⚠️ Data tidak tersedia.")
        return

    # Ikon untuk masing-masing ticker
    ticker_icons = {
        "USD/IDR": "💵",
        "Gold (XAU/USD)": "🥇",
        "Oil (Brent)": "🛢️",
        "Bitcoin (BTC/USD)": "🪙"
    }

    # Format hasil dengan cek tipe angka
    ticker_str = " | ".join([
        f"{ticker_icons.get(k, '')} {k}: {f'{v:,}' if isinstance(v, (int, float)) else v}"
        for k, v in data.items() if v is not None
    ])

    # Tampilkan running text
    st.markdown(
        f"""
        <marquee behavior="scroll" direction="left" scrollamount="5" style="
            background-color: #e6f7ff;
            color: #003366;
            font-weight: bold;
            padding: 8px;
            border-bottom: 1px solid #99ccff;
        ">
            📈 {ticker_str}
        </marquee>
        """,
        unsafe_allow_html=True
    )


def pilih_modul(nama_modul):
    st.session_state["modul_aktif"] = nama_modul
    st.rerun()

def render_modul_button(label, key_prefix="btn"):
    """
    Tombol sidebar dengan highlight biru jika modul aktif.
    """
    is_active = st.session_state.get("modul_aktif") == label

    if is_active:
        st.markdown(
            f"""
            <div style="margin-bottom: 10px;">
                <button style="
                    background-color: #e0f0ff;
                    color: black;
                    border: 1px solid #3399ff;
                    padding: 0.5em 1em;
                    width: 100%;
                    text-align: left;
                    border-radius: 5px;
                    font-weight: bold;
                " disabled>{label}</button>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        if st.button(label, key=f"{key_prefix}_{label}"):
            pilih_modul(label)

def tampilkan_copy_session_state():
    """
    Menampilkan isi session_state yang diawali dengan 'copy_'.
    """
    with st.sidebar.expander("🗂️ Daftar Data Lengkap Key 'copy_'"):
        st.markdown("### 🔍 Semua key dengan prefix copy_ dan isinya:")
        copy_keys = {k: v for k, v in st.session_state.items() if k.startswith("copy_")}
        if copy_keys:
            for k, v in copy_keys.items():
                st.markdown(f"**🔑 {k}**")
                if isinstance(v, pd.DataFrame):
                    if not v.empty:
                        st.dataframe(v, use_container_width=True)
                    else:
                        st.info("📭 DataFrame kosong")
                else:
                    st.write(v)
                st.markdown("---")
        else:
            st.write("🚫 Tidak ada key dengan prefix 'copy_'.")

# ============================ #
# 🧠 DATA KONFIGURASI MODUL
# ============================ #
dashboard_modules = {"📊 Dashboard (Auto)": "dashboard"}
profil_modules = {"🏢 Profil Perusahaan": "profil_perusahaan"}
perencanaan_modules = {
    "📌 Strategi Risiko": "strategi_risiko",
    "🎯 Sasaran Strategi Bisnis": "sasaran_strategi_bisnis",
    "📋 Profil Risiko & KRI": "profil_risiko",
    "🧮 Risiko Inherent": "perhitungan_risiko_inherent",
    "🛠️ Perlakuan Risiko": "perlakuan_risiko",
    "⚖️ Risiko Residual": "perhitungan_risiko_residual",
    "💰 Risk Based Budgeting (Auto)": "risk_based_budgeting",
    "🌡️ Heatmap Risiko (Auto)": "heatmap_risiko"
}
update_modules = {"📆 Detail Perlakuan Risiko": "detail_perlakuan_risiko"}
monitoring_modules = {
    "📅 Monitoring & Evaluasi": "monitoring_evaluasi",
    "📋 Loss Event (Insiden)": "loss_event",
    "📘 Organ & Kualifikasi)": "organ_mr_kualifikasi"
  
}

integrasi_modules = {"🧩 Modul Integrasi Data": "data_integrasi"}

all_module_map = {
    **dashboard_modules,
    **profil_modules,
    **perencanaan_modules,
    **update_modules,
    **monitoring_modules,
    **integrasi_modules
}
import time
@st.cache_data(ttl=600)
def get_ticker_data():
    """
    Mengambil data nilai tukar dan komoditas dari Yahoo Finance.
    Gunakan fast_info jika tersedia, fallback ke info jika None.
    """
    def safe_get(ticker_symbol):
        try:
            ticker = yf.Ticker(ticker_symbol)
            value = ticker.fast_info.get("last_price")
            if value is None:
                value = ticker.info.get("regularMarketPrice")
            return value if value is not None else "N/A"
        except Exception:
            return "N/A"

    return {
        "USD/IDR": safe_get("USDIDR=X"),
        "Gold (XAU/USD)": safe_get("XAUUSD=X"),
        "Oil (Brent)": safe_get("BZ=F"),
        "Bitcoin (BTC/USD)": safe_get("BTC-USD")
    }


# ============================ #
# ▶️ MAIN APP
# ============================ #
def main():
    # ------------------ Inisialisasi State ------------------ #
    if "modul_aktif" not in st.session_state:
        st.session_state["modul_aktif"] = None

    # ------------------ Tampilkan Running Text ------------------ #
    tampilkan_running_text()

    # ------------------ Sidebar Navigasi ------------------ #
    pelindo_icon_path = os.path.join("static", "pelindoicon.jpg")
    via_icon_path = os.path.join("static", "via_icon.jpg")

    with st.sidebar:
        with st.expander("1️⃣ Dashboard"):
            for label in dashboard_modules:
                render_modul_button(label, key_prefix="btn_dashboard")

        with st.expander("2️⃣ Profil Perusahaan"):
            for label in profil_modules:
                render_modul_button(label, key_prefix="btn_profil")

        with st.expander("3️⃣ Perencanaan Risiko"):
            for label in perencanaan_modules:
                render_modul_button(label, key_prefix="btn_perencanaan")

        with st.expander("4️⃣ Update Perlakuan Risiko"):
            for label in update_modules:
                render_modul_button(label, key_prefix="btn_update")

        with st.expander("5️⃣ Monitoring & Evaluasi"):
            for label in monitoring_modules:
                render_modul_button(label, key_prefix="btn_monitoring")

        with st.expander("6️⃣ Modul Integrasi Data"):
            for label in integrasi_modules:
                render_modul_button(label, key_prefix="btn_integrasi")

    # ------------------ Konten Utama / Modul Aktif ------------------ #
    selected_module_name = st.session_state.get("modul_aktif")
    if selected_module_name:
        module_filename = all_module_map.get(selected_module_name)
        if module_filename:
            try:
                selected_module = importlib.import_module(f"modules.{module_filename}")
                main_func = getattr(selected_module, "main", None)
                if callable(main_func):
                    main_func()
                else:
                    st.error(f"❌ Modul '{selected_module_name}' tidak memiliki fungsi main().")
            except ModuleNotFoundError:
                st.error(f"❌ Modul '{selected_module_name}' tidak ditemukan!")
            except Exception as e:
                st.error(f"⚠️ Terjadi kesalahan saat memuat modul '{selected_module_name}': {e}")
                st.text(traceback.format_exc())
        else:
            st.info("ℹ️ Modul ini belum tersedia.")
    else:
        via_icon_path = os.path.join("static", "via_icon.jpg")  # atau via_icon1.jpg sesuai file kamu

        col1, col2 = st.columns([2, 8])
        with col1:
            if os.path.exists(via_icon_path):
                st.image(via_icon_path, width=150)  # Ukuran besar di sisi kiri
        with col2:
            st.markdown("### Selamat Datang di PRIMA-Ai!")
            st.markdown("### Pelindo Risk Managment Application")

        st.markdown("""
        🚀 Aplikasi berbasis Artificial Intelegent yang dirancang khusus untuk mendukung pengelolaan manajemen risiko sesuai dengan Peraturan Menteri Badan Usaha Milik Negara Nomor PER-2/MBU/03/2023 Tahun 2023 :

        - 📌 Menyusun strategi dan profil risiko  
        - 🧮 Menghitung risiko dan Visualisasi heatmap  
        - 🛠️ Menyusun mitigasi otomatis 
        - 📆 Monitoring dan evaluasi Risik & Organ  
        - 🔄 Integrasi data dari seluruh unit

        💡 Teknologi AI (GPT) mempercepat analisis dan memperkuat pengambilan keputusan berbasis risiko.
        """)

        st.markdown("### 🧭 Cara Menggunakan")
        st.markdown("""
        1. Pilih modul dari sidebar.
        2. Ikuti petunjuk pada setiap modul.
        3. Simpan data atau integrasikan ke sistem pusat.
        """)

    # ------------------ Debug: Tampilkan Session State 'copy_' ------------------ #
    tampilkan_copy_session_state()


# ============================ #
# 🚀 JALANKAN APLIKASI
# ============================ #
if __name__ == "__main__":
    main()