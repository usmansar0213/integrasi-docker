import streamlit as st
import pandas as pd
import datetime
import os
import sys
import importlib
import traceback
from modules.utils import get_user_folder, get_user_file


# ===== Konfigurasi Streamlit Page =====
st.set_page_config(page_title="Aplikasi VIA", layout="wide")
USER_DATA_PATH = "user_data.csv"

# ===== Tambah path folder modules =====
modules_dir = os.path.join(os.path.dirname(__file__), "modules")
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

# ===== Inisialisasi session_state =====
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['current_user'] = None
if 'modul_aktif' not in st.session_state:
    st.session_state['modul_aktif'] = None
if 'users' not in st.session_state:
    st.session_state['users'] = (
        pd.read_csv(USER_DATA_PATH)
        if os.path.exists(USER_DATA_PATH)
        else pd.DataFrame(columns=['User', 'Username', 'Password', 'Waktu Akses Awal', 'Waktu Akses Akhir', 'Role'])
    )

# Tambahan kolom 'Role' jika CSV lama belum memiliki kolom ini
if 'Role' not in st.session_state['users'].columns:
    st.session_state['users']['Role'] = 'user'
if 'Perusahaan' not in st.session_state['users'].columns:
    st.session_state['users']['Perusahaan'] = ""


# ===== Fungsi Login/Register =====
def sign_in():
    st.subheader("Sign In")
    col1, col2 = st.columns([1, 2])
    col1.image("static/pelindoicon.jpg", width=200)
    col1.image("static/via_icon.jpg", width=200)

    col2.title("Selamat Datang di Aplikasi VIA")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = st.session_state['users']
        if not users.empty and username.lower() in users['Username'].str.lower().values:
            user_row = users[users['Username'].str.lower() == username.lower()].iloc[0]
            if user_row['Password'] == password:
                st.session_state['authenticated'] = True
                st.session_state['current_user'] = user_row['Username']
                st.session_state['user_folder'] = get_user_folder()
                users.loc[users['Username'] == user_row['Username'], 'Waktu Akses Awal'] = datetime.datetime.now()
                st.session_state['users'] = users
                users.to_csv(USER_DATA_PATH, index=False)
                st.rerun()
            else:
                st.error("❌ Password salah.")


def sign_up():
    st.subheader("Sign Up")
    col1, col2 = st.columns([1, 2])
    col1.image("static/pelindoicon.jpg", width=200)
    col1.image("static/via_icon.jpg", width=200)

    col2.title("Pendaftaran Akun Baru")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    
    perusahaan_options = [
        "DEMO",
    ]

    selected_perusahaan = st.selectbox("Pilih Nama Perusahaan", perusahaan_options)

    if st.button("Register"):
        users = st.session_state['users']
        if new_username in users['Username'].values:
            st.error("Username already exists.")
        else:
            new_user = pd.DataFrame(
                [[new_username, new_username, new_password, datetime.datetime.now(), None, "user", selected_perusahaan]],
                columns=['User', 'Username', 'Password', 'Waktu Akses Awal', 'Waktu Akses Akhir', 'Role', 'Perusahaan']
            )
            st.session_state['users'] = pd.concat([users, new_user], ignore_index=True)
            st.session_state['users'].to_csv(USER_DATA_PATH, index=False)
            st.success("Registration successful! Please Sign In.")


# ===== Fungsi Modul Navigation =====
def pilih_modul(nama_modul):
    st.session_state["modul_aktif"] = nama_modul
    st.rerun()

def render_modul_button(label, key_prefix="btn"):
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

# ===== Struktur Modul =====
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
    "📋 Loss Event (Insiden)": "loss_event"
}


integrasi_modules = {"🧩 Modul Integrasi Data": "data_integrasi"}
mrtools_modules = {
    "Chat Bot VIA": "chatbot_via",
    "Risk Modeling Monte Carlo": "risk_modeling_montecarlo",
    "RCSA AI": "rcsa_ai",
    "Feasibility Study": "feasibility_study",
    "Stress Testing": "stress_testing",
    "Altman Z-Score": "altmanz_score",
    "Fault Tree Analysis": "fault_tree",
    "Risk Maturity Index": "risk_maturity_index"
}

all_module_map = {
    **dashboard_modules,
    **profil_modules,
    **perencanaan_modules,
    **update_modules,
    **monitoring_modules,
    **integrasi_modules,
    **mrtools_modules
}
def tampilkan_dan_edit_user():
    st.title("🛠️ Manajemen Pengguna")

    # Validasi: hanya admin yang boleh akses
    current_user = st.session_state.get("current_user", "")
    df_users = st.session_state.get("users", pd.DataFrame())

    if df_users.empty or current_user not in df_users['Username'].values:
        st.error("❌ Data pengguna tidak ditemukan.")
        return

    user_data = df_users[df_users["Username"] == current_user].iloc[0]
    if user_data.get("Role", "user") != "admin":
        st.warning("⚠️ Hanya admin yang dapat mengakses halaman ini.")
        return

    # Tampilkan daftar user
    st.markdown("### 📋 Daftar Seluruh Pengguna")
    st.dataframe(df_users[["User", "Username", "Role", "Perusahaan"]], use_container_width=True)

    # Pilih user yang akan diedit
    selected_username = st.selectbox("🔍 Pilih Username untuk Diedit", df_users["Username"].unique())
    selected_user_row = df_users[df_users["Username"] == selected_username].iloc[0]

    st.markdown("### ✏️ Edit Data Pengguna")
    new_name = st.text_input("Nama Lengkap", value=selected_user_row["User"])
    new_password = st.text_input("Password Baru (opsional)", value="", type="password")
    new_role = st.selectbox("Peran", ["user", "admin"], index=["user", "admin"].index(selected_user_row.get("Role", "user")))

    if st.button("💾 Simpan Perubahan"):
        idx = df_users[df_users["Username"] == selected_username].index[0]
        st.session_state["users"].at[idx, "User"] = new_name
        st.session_state["users"].at[idx, "Role"] = new_role
        if new_password:
            st.session_state["users"].at[idx, "Password"] = new_password
        st.session_state["users"].to_csv(USER_DATA_PATH, index=False)
        st.success("✅ Perubahan berhasil disimpan.")

def main():
    if not st.session_state['authenticated']:
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        with tab1: sign_in()
        with tab2: sign_up()
        return

    # ===== Logout Button =====
    if st.button("Logout"):
        users = st.session_state['users']
        users.loc[users['Username'] == st.session_state['current_user'], 'Waktu Akses Akhir'] = datetime.datetime.now()
        st.session_state['users'] = users
        users.to_csv(USER_DATA_PATH, index=False)
        for key in ["authenticated", "current_user", "modul_aktif", "user_folder", "last_menu_selection"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # ===== Sidebar Navigasi =====
        # ===== Sidebar Navigasi =====
    with st.sidebar:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.image("static/pelindoicon.jpg", width=200)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(f"👤 **User:** `{st.session_state['current_user']}`")

        # Ambil info user & perusahaan
        df_users = st.session_state["users"]
        current_user = st.session_state["current_user"]
        if current_user in df_users["Username"].values:
            user_row = df_users[df_users["Username"] == current_user].iloc[0]
            perusahaan_user = user_row.get("Perusahaan", "")
            st.markdown(f"🏢 **Perusahaan:** `{perusahaan_user}`")

            # Admin panel
            if user_row.get("Role", "user") == "admin":
                st.markdown("## 👤 Admin Panel")
                if st.button("🔧 Manajemen Pengguna"):
                    st.session_state["modul_aktif"] = "manajemen_pengguna"

        # 👉 PINDAHKAN NAVIGASI KE SINI
        st.markdown("### 🧭 Navigasi")
        menu_selection = st.radio("📌 Halaman Utama", ["Landing Page", "MR Tools", "PRIMA-Ai"], key="menu_selection")

    # ===== Menu Utama =====

    if "last_menu_selection" not in st.session_state:
        st.session_state["last_menu_selection"] = None

    if menu_selection != st.session_state["last_menu_selection"]:
        if menu_selection == "MR Tools":
            st.session_state["modul_aktif"] = None
        st.session_state["last_menu_selection"] = menu_selection

    if menu_selection == "Landing Page":
        import modules.landing_page as landing_page
        landing_page.show()

    elif menu_selection == "MR Tools":
        with st.sidebar:
            with st.expander("1️⃣ Chat Bot VIA"):
                render_modul_button("Chat Bot VIA", key_prefix="btn_mrtools")
            with st.expander("2️⃣ Risk Modeling Monte Carlo"):
                render_modul_button("Risk Modeling Monte Carlo", key_prefix="btn_mrtools")
            with st.expander("3️⃣ RCSA AI"):
                render_modul_button("RCSA AI", key_prefix="btn_mrtools")
            with st.expander("4️⃣ Feasibility Study"):
                render_modul_button("Feasibility Study", key_prefix="btn_mrtools")
            with st.expander("5️⃣ Stress Testing"):
                render_modul_button("Stress Testing", key_prefix="btn_mrtools")
            with st.expander("6️⃣ Altman Z-Score"):
                render_modul_button("Altman Z-Score", key_prefix="btn_mrtools")
            with st.expander("7️⃣ Risk Maturity Index"):
                render_modul_button("Risk Maturity Index", key_prefix="btn_mrtools")
            with st.expander("8️⃣ Fault Tree Analysis"):
                render_modul_button("Fault Tree Analysis", key_prefix="btn_mrtools")

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
            col1, col2 = st.columns([2, 8])
            via_icon_path = os.path.join("static", "via_icon.jpg")
            with col1:
                if os.path.exists(via_icon_path):
                    st.image(via_icon_path, width=150)
            with col2:
                st.markdown("### Selamat Datang di MR Tools!")
                st.markdown("### Tools Manajemen Risiko berbasis AI untuk berbagai kebutuhan")
            st.markdown("""
            🚀 Berikut adalah daftar modul yang tersedia di *MR Tools*, yang dirancang untuk mendukung manajemen risiko dan pengambilan keputusan berbasis data dan AI:

            1. 🤖 **Chat Bot VIA**  
               VIA adalah asisten virtual pintar yang membantu dalam berbagai analisis risiko dan pengambilan keputusan berbasis data.

            2. 🎲 **Risk Modeling Monte Carlo**  
               Monte Carlo simulation digunakan untuk memproyeksikan berbagai kemungkinan hasil berdasarkan variabel yang ada.

            3. 🧠 **RCSA AI**  
               Mengotomatiskan identifikasi dan pemantauan risiko dengan teknologi AI.

            4. 📊 **Feasibility Study**  
               Studi kelayakan proyek dari sisi finansial, hukum, operasional, dan lingkungan.

            5. 💣 **Stress Testing**  
               Uji ketahanan perusahaan terhadap skenario ekstrem.

            6. 🧮 **Altman Z-Score**  
               Model statistik untuk prediksi kebangkrutan perusahaan.

            7. 📈 **Risk Maturity Index**  
               Mengukur tingkat kematangan manajemen risiko.
            """)
            st.markdown("### 🧭 Cara Menggunakan")
            st.markdown("""
            1. Pilih salah satu modul dari sidebar kiri.
            2. Ikuti petunjuk yang tersedia di masing-masing modul.
            3. Simpan atau ekspor hasil sesuai kebutuhan.
            """)
            
    # === PRIMA-Ai ===
    elif menu_selection == "PRIMA-Ai":
        try:
            sys.path.append(r"C:\Users\usman\aplikasi MR")
            import main_mr
            main_mr.main()
        except Exception as e:
            st.error(f"❌ Gagal membuka PRIMA-Ai: {e}")
            st.text(traceback.format_exc())
    # Jalankan modul manajemen pengguna (khusus admin)
    if st.session_state.get("modul_aktif") == "manajemen_pengguna":
        tampilkan_dan_edit_user()


# ===== Jalankan App =====
if __name__ == '__main__':
    main()
