import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime
import difflib
from difflib import SequenceMatcher
import re


def load_all_data_from_uploaded_files(uploaded_files):
    df_integrasi_list = []
    df_loss_list = []
    df_kual_list = []

    for file in uploaded_files:
        filename = file.name.lower()
        try:
            df = pd.read_excel(file)
            df["Sumber File"] = file.name

            if re.search(r"risk[_ ]?monitoring|monitoring", filename):
                df_integrasi_list.append(df)
            elif "loss_event" in filename:
                df_loss_list.append(df)
            elif "kualifikasi" in filename:
                df_kual_list.append(df)
            else:
                st.warning(f"⚠️ File `{file.name}` tidak dikenali sebagai data integrasi/loss_event/kualifikasi.")
        except Exception as e:
            st.warning(f"⚠️ Gagal membaca `{file.name}`: {e}")

    df_integrasi = pd.concat(df_integrasi_list, ignore_index=True) if df_integrasi_list else pd.DataFrame()
    df_loss = pd.concat(df_loss_list, ignore_index=True) if df_loss_list else pd.DataFrame()
    df_kual = pd.concat(df_kual_list, ignore_index=True) if df_kual_list else pd.DataFrame()

    return df_integrasi, df_loss, df_kual

def tampilkan_data_integrasi(df: pd.DataFrame, judul: str = "📄 Data Integrasi Risiko"):
    st.subheader("📊 Dashboard Monitoring Risiko")
    with st.expander(judul, expanded=True):
        if df.empty:
            st.warning("⚠️ Data integrasi tidak tersedia atau kosong.")
        else:
            st.dataframe(df, use_container_width=True)


def filter_risiko_interaktif(df):
    st.markdown("### 🔍 Filter Risiko")

    # ========== Baris 1: Multiselect Perusahaan ==========
    perusahaan_terpilih = st.multiselect(
        "Pilih Perusahaan",
        options=sorted(df["Nama Perusahaan"].dropna().unique()),
        default=[]  # bisa dikosongkan (berarti semua)
    )

    # ========== Baris 2: Tahun, Bulan, Divisi ==========
    col1, col2, col3 = st.columns(3)

    with col1:
        tahun = st.selectbox(
            "Tahun",
            sorted(df["Tahun Pelaporan"].dropna().unique()),
            index=0
        )

    with col2:
        bulan = st.selectbox(
            "Bulan",
            sorted(df["Bulan Pelaporan"].dropna().unique()),
            index=0
        )

    with col3:
        divisi = st.selectbox(
            "Divisi",
            sorted(df["Divisi"].dropna().unique()),
            index=0
        )

    # ========== Proses Filter ==========
    df_filtered = df[
        (df["Tahun Pelaporan"] == tahun) &
        (df["Bulan Pelaporan"] == bulan) &
        (df["Divisi"] == divisi)
    ]

    if perusahaan_terpilih:
        df_filtered = df_filtered[df_filtered["Nama Perusahaan"].isin(perusahaan_terpilih)]

    # Simpan hasil filter perusahaan ke session_state
    st.session_state["filter_perusahaan"] = perusahaan_terpilih

    # ========== Tampilkan Hasil ==========
    with st.expander("📄 Lihat Data Terfilter", expanded=False):
        if not df_filtered.empty:
            st.dataframe(df_filtered, use_container_width=True)
        else:
            st.warning("⚠️ Tidak ada data yang sesuai dengan filter.")

    return df_filtered


# -------------------- Fungsi Heatmap --------------------
def tampilkan_matriks_risiko(df, title="🌡️ Heatmap Matriks Risiko Monitoring", x_label="Skala Dampak", y_label="robabilitas Saat ini"):
    st.subheader(title)

    risk_labels = {
        (1, 1): ('Low', 1), (1, 2): ('Low', 5), (1, 3): ('Low to Moderate', 10), (1, 4): ('Moderate', 15), (1, 5): ('High', 20),
        (2, 1): ('Low', 2), (2, 2): ('Low to Moderate', 6), (2, 3): ('Low to Moderate', 11), (2, 4): ('Moderate to High', 16), (2, 5): ('High', 21),
        (3, 1): ('Low', 3), (3, 2): ('Low to Moderate', 8), (3, 3): ('Moderate', 13), (3, 4): ('Moderate to High', 18), (3, 5): ('High', 23),
        (4, 1): ('Low', 4), (4, 2): ('Low to Moderate', 9), (4, 3): ('Moderate', 14), (4, 4): ('Moderate to High', 19), (4, 5): ('High', 24),
        (5, 1): ('Low to Moderate', 7), (5, 2): ('Moderate', 12), (5, 3): ('Moderate to High', 17), (5, 4): ('High', 22), (5, 5): ('High', 25)
    }

    color_matrix = np.full((5, 5), 'white', dtype=object)
    risk_matrix = [['' for _ in range(5)] for _ in range(5)]

    for coord, (label, _) in risk_labels.items():
        i, j = coord[0] - 1, coord[1] - 1
        color_matrix[i][j] = {
            'High': 'red',
            'Moderate to High': 'orange',
            'Moderate': 'yellow',
            'Low to Moderate': 'lightgreen',
            'Low': 'darkgreen'
        }.get(label, 'white')

    for _, row in df.iterrows():
        try:
            prob = int(row.get('Probabilitas Saat Ini', 0))
            damp = int(row.get('Skala Dampak Saat Ini', 0))
            no_risiko = f"#{int(row['Nomor Risiko_y'])}" if 'Nomor Risiko_y' in row and pd.notnull(row['Nomor Risiko_y']) else ''

            i = prob - 1
            j = damp - 1
            if 0 <= i < 5 and 0 <= j < 5:
                existing = risk_matrix[i][j].replace("\n", ", ").split(", ") if risk_matrix[i][j] else []
                if no_risiko and no_risiko not in existing:
                    existing.append(no_risiko)
                lines = [", ".join(existing[k:k+4]) for k in range(0, len(existing), 4)]
                risk_matrix[i][j] = "\n".join(lines)
        except:
            continue

    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    for i in range(5):
        for j in range(5):
            ax.add_patch(plt.Rectangle((j, i), 1, 1, color=color_matrix[i][j], edgecolor='black'))
            label, number = risk_labels.get((i + 1, j + 1), ('', ''))
            ax.text(j + 0.5, i + 0.7, label, ha='center', va='center', fontsize=5)
            ax.text(j + 0.5, i + 0.5, str(number), ha='center', va='center', fontsize=5)
            ax.text(j + 0.5, i + 0.3, risk_matrix[i][j], ha='center', va='center', fontsize=8, color='blue')

    ax.set_xlim(0, 5)
    ax.set_ylim(0, 5)
    ax.set_xticks(np.arange(5) + 0.5)
    ax.set_yticks(np.arange(5) + 0.5)
    ax.set_xticklabels([1, 2, 3, 4, 5], fontsize=7)
    ax.set_yticklabels([1, 2, 3, 4, 5], fontsize=7)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)
    plt.tight_layout()
    st.pyplot(fig)
    
def tampilkan_ringkasan_risiko_terpilih(df_filtered):
    st.subheader("📋 Ringkasan Risiko Terpilih")

    kolom_risiko_terpilih = [
        "Nomor Risiko_y", 
        "Peristiwa Risiko_KRI", 
        "Probabilitas Saat Ini", 
        "Skala Dampak Saat Ini", 
        "Jenis Program Dalam RKAP",
        "Progress Program Mitigasi (%)"
    ]

    if all(kol in df_filtered.columns for kol in kolom_risiko_terpilih):
        df_ringkasan = df_filtered[kolom_risiko_terpilih].copy()
        with st.expander("📄 Lihat Tabel Ringkasan Risiko"):
            st.dataframe(df_ringkasan, use_container_width=True)
    else:
        st.warning("⚠️ Beberapa kolom tidak ditemukan di data terfilter.")

def buat_tabel_distribusi_exposure_per_kode_risiko(df):
    kolom_wajib = ["Kode Perusahaan", "Kode Risiko", "Skala Dampak Saat Ini", "Probabilitas Saat Ini"]
    if not all(k in df.columns for k in kolom_wajib):
        st.warning("⚠️ Kolom penting tidak ditemukan.")
        return pd.DataFrame()

    df["Skala Dampak Saat Ini"] = pd.to_numeric(df["Skala Dampak Saat Ini"], errors="coerce")
    df["Probabilitas Saat Ini"] = pd.to_numeric(df["Probabilitas Saat Ini"], errors="coerce")
    df["Eksposur Risiko"] = df["Skala Dampak Saat Ini"] * df["Probabilitas Saat Ini"]
    df = df.dropna(subset=["Kode Perusahaan", "Kode Risiko", "Eksposur Risiko"])

    tabel = df.pivot_table(
        index="Kode Perusahaan",
        columns="Kode Risiko",
        values="Eksposur Risiko",
        aggfunc="mean"
    ).fillna("")

    # Urutkan dengan prioritas "PLND" jika ada
    indeks = list(tabel.index)
    if "PLND" in indeks:
        urutan_custom = ["PLND"] + [x for x in indeks if x != "PLND"]
        tabel = tabel.loc[urutan_custom]
    else:
        tabel = tabel.sort_index()

    return tabel


def style_warna_sama_dengan_heatmap(val):
    try:
        val = float(val)
        if val >= 20:
            color = 'red'
        elif val >= 15:
            color = 'orange'
        elif val >= 10:
            color = 'yellow'
        elif val >= 5:
            color = 'lightgreen'
        elif val >= 1:
            color = 'darkgreen'
        else:
            color = 'white'
        return f'background-color: {color}; text-align: center'
    except:
        return 'background-color: white; text-align: center'
def buat_tabel_keterangan_risiko(df):
    """
    Menghasilkan tabel keterangan risiko berisi: Kode Risiko dan Peristiwa Risiko_KRI.
    Hanya mengambil kombinasi unik.
    """
    if not all(k in df.columns for k in ["Kode Risiko", "Peristiwa Risiko_KRI"]):
        st.warning("⚠️ Kolom 'Kode Risiko' atau 'Peristiwa Risiko_KRI' tidak ditemukan.")
        return pd.DataFrame()

    tabel = df[["Kode Risiko", "Peristiwa Risiko_KRI"]].drop_duplicates().dropna()
    return tabel.sort_values("Kode Risiko")



def siapkan_target_quarter(df):
    # Hitung kuartal saat ini
    quarter = (datetime.now().month - 1) // 3 + 1

    df = df.copy()
    df["Nilai Eksposur Risiko"] = pd.to_numeric(df.get("Nilai Eksposur Risiko"), errors="coerce")
    df["Progress Program Mitigasi (%)"] = pd.to_numeric(df.get("Progress Program Mitigasi (%)"), errors="coerce")

    df["Eksposur Risiko Target Quarter"] = (df["Nilai Eksposur Risiko"] / 4) * quarter
    df["Target Progress Quarter"] = 25 * quarter

    return df
def early_warning_indicator(df):
    st.subheader("🚨 Early Warning Indicator")
    df = siapkan_target_quarter(df)

    # Fallback kolom penting dari session_state
    df_info = st.session_state.get("copy_informasi_perusahaan", pd.DataFrame())
    info_dict = {}
    if isinstance(df_info, pd.DataFrame) and not df_info.empty:
        for _, row in df_info.iterrows():
            info_dict[row["Data yang dibutuhkan"]] = row["Input Pengguna"]

    def fallback_kolom(df, kolom):
        if kolom not in df.columns or df[kolom].dropna().astype(str).str.strip().eq("").all():
            df[kolom] = info_dict.get(kolom, "NA")
        return df

    for kolom in ["Nomor Risiko_y", "Nama Perusahaan", "Divisi", "Peristiwa Risiko_KRI"]:
        df = fallback_kolom(df, kolom)

    # 🔥 Eksposur Melebihi Target
    with st.expander("🔥 Risiko Eksposur Melebihi Target Quarter", expanded=False):
        data1, err1 = get_risiko_eksposur_tinggi(df)
        if err1:
            st.warning(f"⚠️ {err1}")
        elif data1.empty:
            st.info("✅ Tidak ada risiko dengan eksposur melebihi target.")
        else:
            st.dataframe(data1, use_container_width=True)

    # 🧯 Progress Mitigasi Rendah
    with st.expander("🧯 Risiko dengan Progress Program Mitigasi di Bawah Target", expanded=False):
        data2, err2 = get_progress_mitigasi_rendah(df)
        if err2:
            st.warning(f"⚠️ {err2}")
        elif data2.empty:
            st.info("✅ Tidak ada risiko dengan progress program mitigasi di bawah target.")
        else:
            st.dataframe(data2, use_container_width=True)

    # ⚠️ KRI Kurang
    with st.expander("⚠️ Risiko dengan Status KRI 'Kurang'", expanded=False):
        data3, err3 = get_kri_kurang(df)
        if err3:
            st.warning(f"⚠️ {err3}")
        elif data3.empty:
            st.info("✅ Tidak ada risiko dengan status KRI 'Kurang'.")
        else:
            st.dataframe(data3, use_container_width=True)

def get_risiko_eksposur_tinggi(df):
    kolom_dibutuhkan = ["Nomor Risiko_y", "Nama Perusahaan", "Divisi", "Peristiwa Risiko_KRI", "Probabilitas Saat Ini", "Skala Dampak Saat Ini", "Eksposur Risiko Target Quarter"]
    missing = [k for k in kolom_dibutuhkan if k not in df.columns]
    if missing:
        return pd.DataFrame(), f"Kolom hilang: {missing}"

    df = df.copy()
    df["Probabilitas Saat Ini"] = pd.to_numeric(df.get("Probabilitas Saat Ini"), errors="coerce")
    df["Skala Dampak Saat Ini"] = pd.to_numeric(df.get("Skala Dampak Saat Ini"), errors="coerce")
    df["Eksposur Risiko"] = df["Probabilitas Saat Ini"] * df["Skala Dampak Saat Ini"]
    hasil = df[df["Eksposur Risiko"] > df["Eksposur Risiko Target Quarter"]]

    return hasil[[
        "Nomor Risiko_y", "Nama Perusahaan", "Divisi", "Peristiwa Risiko_KRI",
        "Eksposur Risiko", "Eksposur Risiko Target Quarter"
    ]], None


# Indikator 2: Progress Mitigasi < Target
def get_progress_mitigasi_rendah(df):
    if "Progress Program Mitigasi (%)" not in df.columns or "Target Progress Quarter" not in df.columns:
        return None, "Kolom 'Progress Program Mitigasi (%)' atau 'Target Progress Quarter' tidak ditemukan."
    hasil = df[df["Progress Program Mitigasi (%)"] < df["Target Progress Quarter"]]
    return hasil[[
        "Nomor Risiko_y", "Nama Perusahaan", "Divisi", "Peristiwa Risiko_KRI",
        "Progress Program Mitigasi (%)", "Target Progress Quarter"
    ]], None

# Indikator 3: KRI "Kurang"
def get_kri_kurang(df):
    kolom_kri = None
    if "Status KRI" in df.columns:
        kolom_kri = "Status KRI"
    elif "Pengelolaan KRI" in df.columns:
        kolom_kri = "Pengelolaan KRI"
    else:
        return None, "Kolom 'Status KRI' atau 'Pengelolaan KRI' tidak ditemukan."
    hasil = df[df[kolom_kri].astype(str).str.lower().str.strip() == "kurang"]
    return hasil[[
        "Nomor Risiko_y", "Nama Perusahaan", "Divisi", "Peristiwa Risiko_KRI", kolom_kri
    ]], None

def tampilkan_loss_event(df_filtered):
    with st.expander("📉 Rekap Loss Event", expanded=False):
        df_loss = st.session_state.get("database_loss_event", pd.DataFrame())
        if df_loss.empty:
            st.warning("⚠️ Tidak ada database loss event yang tersedia.")
            return

        perusahaan_dipilih = st.session_state.get("filter_perusahaan", [])
        if not perusahaan_dipilih:
            st.info("ℹ️ Tidak ada filter diterapkan. Menampilkan seluruh data loss event.")
            st.dataframe(df_loss, use_container_width=True)
            return

        nama_perusahaan = df_filtered["Nama Perusahaan"].iloc[0] if "Nama Perusahaan" in df_filtered.columns else None
        tahun = df_filtered["Tahun Pelaporan"].iloc[0] if "Tahun Pelaporan" in df_filtered.columns else None
        bulan = df_filtered["Bulan Pelaporan"].iloc[0] if "Bulan Pelaporan" in df_filtered.columns else None
        divisi = df_filtered["Divisi"].iloc[0] if "Divisi" in df_filtered.columns else None

        df_result = df_loss.copy()

        if nama_perusahaan and "Nama Perusahaan" in df_result.columns:
            df_result = df_result[df_result["Nama Perusahaan"].astype(str).str.strip() == str(nama_perusahaan).strip()]
        if tahun and "Tahun Pelaporan" in df_result.columns:
            df_result = df_result[df_result["Tahun Pelaporan"] == tahun]
        if bulan and "Bulan Pelaporan" in df_result.columns:
            df_result = df_result[df_result["Bulan Pelaporan"] == bulan]
        if divisi and "Divisi" in df_result.columns:
            df_result = df_result[df_result["Divisi"].astype(str).str.strip() == str(divisi).strip()]

        if df_result.empty:
            st.warning("⚠️ Tidak ada data loss event sesuai filter.")
        else:
            st.success(f"✅ {len(df_result)} baris data loss event ditemukan.")
            st.dataframe(df_result, use_container_width=True)

def tampilkan_database_loss_dan_kualifikasi():
   # ------------------ Loss Event ------------------ #
    df_loss = st.session_state.get("database_loss_event", pd.DataFrame())
    with st.expander("📉 Lihat Database Loss Event", expanded=False):
        if df_loss.empty:
            st.info("⚠️ Database loss event masih kosong.")
        else:
            st.write(f"Total Baris: {len(df_loss)}")
            st.dataframe(df_loss, use_container_width=True)

def tampilkan_kualifikasi_terbaru(df_filtered):
    with st.expander("📋 Data Kualifikasi Terbaru", expanded=False):
        df_kual = st.session_state.get("database_kualifikasi", pd.DataFrame())
        if df_kual.empty:
            st.warning("⚠️ Tidak ada database kualifikasi yang tersedia.")
            return

        perusahaan_dipilih = st.session_state.get("filter_perusahaan", [])
        if not perusahaan_dipilih:
            st.info("ℹ️ Tidak ada filter perusahaan. Menampilkan seluruh data kualifikasi.")
            st.dataframe(df_kual, use_container_width=True)
            return

        nama_perusahaan = df_filtered["Nama Perusahaan"].iloc[0] if "Nama Perusahaan" in df_filtered.columns else None
        df_result = df_kual.copy()

        kolom_perusahaan_kual = "Nama Perusahaan" if "Nama Perusahaan" in df_result.columns else (
            "Perusahaan" if "Perusahaan" in df_result.columns else None
        )

        if nama_perusahaan and kolom_perusahaan_kual:
            df_result = df_result[df_result[kolom_perusahaan_kual].astype(str).str.strip() == str(nama_perusahaan).strip()]

        if df_result.empty:
            st.warning("⚠️ Tidak ada data kualifikasi sesuai filter.")
        else:
            st.success(f"✅ {len(df_result)} baris data kualifikasi ditemukan.")
            st.dataframe(df_result, use_container_width=True)

def main():
    st.title("📊 Dashboard Monitoring Risiko")

    # ======== 0. Upload File Semua Sekaligus ======== #
    uploaded_files = st.file_uploader(
        "Silakan upload 3 file : Kualifikasi_organ , loss_event, monitoring",
        type=["xlsx"],
        accept_multiple_files=True,
        key="uploaded_files_dashboard"
    )

    if not uploaded_files:
        st.warning("⚠️ Silakan upload 3 file : Kualifikasi_organ , loss_event, monitoring")
        return

    # ======== 1. Load data dari uploaded_files ======== #
    df_integrasi, df_loss_event, df_kualifikasi = load_all_data_from_uploaded_files(uploaded_files)

    # ======== 2. Validasi keberadaan tiga file utama ======== #
    if df_integrasi.empty:
        st.error("❌ File `risk_monitoring` belum ditemukan atau tidak berisi data yang valid.")
    if df_loss_event.empty:
        st.error("❌ File `loss_event` belum ditemukan atau tidak berisi data yang valid.")
    if df_kualifikasi.empty:
        st.error("❌ File `kualifikasi` belum ditemukan atau tidak berisi data yang valid.")
    if df_integrasi.empty or df_loss_event.empty or df_kualifikasi.empty:
        st.stop()  # 🔴 Hentikan eksekusi jika salah satu file belum tersedia

    # ======== 3. Simpan ke session_state ======== #
    st.session_state["data_integrasi"] = df_integrasi
    st.session_state["database_loss_event"] = df_loss_event
    st.session_state["database_kualifikasi"] = df_kualifikasi


    # ======== 2. Tampilkan Data Integrasi ======== #
    if df_integrasi.empty:
        st.warning("⚠️ Data integrasi tidak tersedia.")
        return

    with st.expander("📄 Lihat Data Integrasi Risiko", expanded=False):
        st.dataframe(df_integrasi, use_container_width=True)

    # ======== 3. Filter Interaktif ========= #
    df_filtered = filter_risiko_interaktif(df_integrasi)

    st.markdown("---")

    # ======== 4. Early Warning ========= #
    df_filtered = siapkan_target_quarter(df_filtered)
    early_warning_indicator(df_filtered)

    st.markdown("---")

    # ======== 5. Heatmap Risiko ========= #
    if "Skala Dampak Saat Ini" in df_filtered.columns and "Probabilitas Saat Ini" in df_filtered.columns:
        tampilkan_matriks_risiko(df_filtered)
    else:
        st.warning("⚠️ Kolom skala dampak/probabilitas belum tersedia.")

    # ======== 6. Ringkasan Risiko ========= #
    tampilkan_ringkasan_risiko_terpilih(df_filtered)

    # ======== 7. Distribusi Eksposur ========= #
    with st.expander("📊 Distribusi Eksposur Risiko Antar Perusahaan", expanded=False):
        tabel_distribusi_exposure = buat_tabel_distribusi_exposure_per_kode_risiko(df_filtered)
        if not tabel_distribusi_exposure.empty:
            st.dataframe(
                tabel_distribusi_exposure.style.applymap(style_warna_sama_dengan_heatmap),
                use_container_width=True
            )
        else:
            st.info("Tidak ada data distribusi eksposur yang tersedia.")

    # ======== 8. Keterangan Risiko ========= #
    with st.expander("📘 Keterangan Kode Risiko", expanded=False):
        tabel_keterangan = buat_tabel_keterangan_risiko(df_filtered)
        if not tabel_keterangan.empty:
            st.dataframe(tabel_keterangan, use_container_width=True)
        else:
            st.info("Tidak ada data keterangan risiko yang tersedia.")

    st.markdown("---")

    # ======== 9. Rekap Loss Event ========= #
    tampilkan_loss_event(df_filtered)

    # ======== 10. Kualifikasi Terbaru ========= #
    tampilkan_kualifikasi_terbaru(df_filtered)

    st.markdown("---")




if __name__ == "__main__":
    main()
