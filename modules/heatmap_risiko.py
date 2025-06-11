import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def load_file_inherent_residual():
    with st.expander("📥 Upload File Risiko Inherent & Residual", expanded=True):
        uploaded_files = st.file_uploader(
            "Unggah 2 file: 1) Inherent_Dampak dan 2) Residual_Dampak", 
            type=["xlsx"], 
            accept_multiple_files=True,
            key="upload_inherent_residual"
        )

        file_inherent = None
        file_residual = None

        for f in uploaded_files:
            xls = pd.ExcelFile(f)
            sheet_names = [s.lower() for s in xls.sheet_names]
            if "tabel kuantitatif" in sheet_names or "tabel kualitatif" in sheet_names:
                file_inherent = f
            elif "residual_dampak" in sheet_names or "residual_prob" in sheet_names:
                file_residual = f

        # === Load Inherent Risk
        if file_inherent:
            xls_inherent = pd.ExcelFile(file_inherent)
            for sheet in xls_inherent.sheet_names:
                sheet_lower = sheet.lower()
                df = pd.read_excel(xls_inherent, sheet_name=sheet)
                if "kuantitatif" in sheet_lower:
                    st.session_state["copy_risiko_kuantitatif"] = df
                elif "kualitatif" in sheet_lower:
                    st.session_state["copy_risiko_kualitatif"] = df

        # === Load Residual Risk
        if file_residual:
            xls_residual = pd.ExcelFile(file_residual)
            for sheet in xls_residual.sheet_names:
                sheet_lower = sheet.lower()
                df = pd.read_excel(xls_residual, sheet_name=sheet)
                if "residual_dampak" in sheet_lower:
                    st.session_state["copy_tabel_dampak_q1"] = df
                elif "residual_prob" in sheet_lower:
                    st.session_state["copy_tabel_probabilitas_q1"] = df


def init_session_state():
    default_values = {
        'copy_metrix_strategi_risiko': pd.DataFrame(columns=["Kode Risiko", "Peristiwa Risiko", "Satuan Ukuran", "Nilai Batasan/Limit"]),
        'copy_deskripsi_risiko': pd.DataFrame(columns=["Kode Risiko", "Peristiwa Risiko", "Deskripsi Peristiwa Risiko", "No. Penyebab Risiko", "Kode Penyebab Risiko", "Penyebab Risiko"]),
        'copy_tabel_gabungan': pd.DataFrame(columns=["Kode Risiko", "Limit Risiko", "Peristiwa Risiko"]),
        'copy_perhitungan_risiko': pd.DataFrame(columns=["Kode Risiko", "Limit Risiko", "Peristiwa Risiko", "Penjelasan Dampak", "Nilai Dampak", "Skala Dampak", "Nilai Probabilitas", "Skala Probabilitas", "Nilai Eksposur Risiko", "Skala Risiko", "Level Nilai Risiko", "Jenis Dampak"]),
        'copy_control_dampak': pd.DataFrame(columns=["Kode Risiko", "Jenis Existing Control", "Existing Control", "Penilaian Efektivitas Kontrol", "Kategori Dampak", "Deskripsi Dampak", "Perkiraan Waktu Terpapar Risiko"]),
        'copy_limit_risiko': "Belum Ditentukan",
        'copy_risiko_kuantitatif': pd.DataFrame(),
        'copy_risiko_kualitatif': pd.DataFrame(),
        'copy_tabel_residual_q1': pd.DataFrame(),
        'copy_tabel_dampak_q1': pd.DataFrame(),
        'copy_tabel_probabilitas_q1': pd.DataFrame()
    }
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value


def persist_updated_data():
    if "temp_risiko_kuantitatif" in st.session_state:
        st.session_state["copy_risiko_kuantitatif"] = st.session_state["temp_risiko_kuantitatif"].copy()
    if "temp_risiko_kualitatif" in st.session_state:
        st.session_state["copy_risiko_kualitatif"] = st.session_state["temp_risiko_kualitatif"].copy()

def merge_tables():
    if 'copy_risiko_kuantitatif' in st.session_state and 'copy_risiko_kualitatif' in st.session_state:
        df_kuantitatif = st.session_state['copy_risiko_kuantitatif'].copy()
        df_kualitatif = st.session_state['copy_risiko_kualitatif'].copy()

        df_kuantitatif['Tipe Risiko'] = 'Kuantitatif'
        df_kualitatif['Tipe Risiko'] = 'Kualitatif'

        merged_df = pd.concat([df_kuantitatif, df_kualitatif], ignore_index=True)

        rename_mapping = {
            "Skala Dampak BUMN": "Skala Dampak",
            "Skala Probabilitas BUMN": "Skala Probabilitas",
            "Nilai Dampak": "Nilai Dampak",
            "Nilai Probabilitas": "Nilai Probabilitas",
            "Eksposur Risiko": "Nilai Eksposur Risiko"
        }
        merged_df.rename(columns=rename_mapping, inplace=True)

        st.session_state["copy_tabel_gabungan"] = merged_df
        return merged_df
    return pd.DataFrame()
 

def tampilkan_matriks_risiko(df, title="Heatmap Matriks Risiko", x_label="Skala Dampak", y_label="Skala Kemungkinan"):
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
            i = int(row['Skala Probabilitas']) - 1
            j = int(row['Skala Dampak']) - 1
            nomor = f"#{int(row['No'])}" if 'No' in row else ''
            if 0 <= i < 5 and 0 <= j < 5:
                existing = risk_matrix[i][j].replace("\n", ", ").split(", ") if risk_matrix[i][j] else []
                if nomor and nomor not in existing:
                    existing.append(nomor)
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
    
def gabungkan_residual_q1():
    df_prob = st.session_state.get("copy_tabel_probabilitas_q1", pd.DataFrame())
    df_dampak = st.session_state.get("copy_tabel_dampak_q1", pd.DataFrame())

    if df_prob.empty or df_dampak.empty:
        st.warning("⚠️ Salah satu dari tabel residual probabilitas atau dampak kosong.")
        return pd.DataFrame()

    df_prob_renamed = df_prob.rename(columns={"Skala Q1": "Skala Probabilitas Q1"})
    df_dampak_renamed = df_dampak.rename(columns={"Skala Q1": "Skala Dampak Q1"})

    df_gabungan = pd.merge(
        df_prob_renamed,
        df_dampak_renamed,
        on="Kode Risiko",
        how="inner",
        suffixes=('_Probabilitas', '_Dampak')
    )

    if "Nomor" in df_gabungan.columns:
        df_gabungan.rename(columns={"Nomor": "No"}, inplace=True)
    else:
        df_gabungan["No"] = range(1, len(df_gabungan) + 1)

    st.session_state["copy_tabel_residual_q1"] = df_gabungan
    return df_gabungan


    return df_gabungan


def tampilkan_heatmap_residual_q1():

    df = st.session_state.get("copy_tabel_residual_q1", pd.DataFrame())

    if df.empty:
        st.warning("⚠️ Tabel residual Q1 belum tersedia.")
        return

    # Cek kolom penting
    if "Skala Probabilitas Q1" not in df.columns or "Skala Dampak Q1" not in df.columns:
        st.error("❌ Kolom 'Skala Probabilitas Q1' atau 'Skala Dampak Q1' tidak ditemukan.")
        return
    if "No" not in df.columns:
        st.error("❌ Kolom 'No' tidak ditemukan untuk label risiko.")
        return

    df["No"] = pd.to_numeric(df["No"], errors="coerce").fillna(0).astype(int)

    st.subheader("Heatmap Matriks Risiko Residual Q1")

    # Inisialisasi matriks
    color_matrix = np.full((5, 5), 'white', dtype=object)
    risk_matrix = [['' for _ in range(5)] for _ in range(5)]

    # Mapping warna dan label risiko
    label_colors = {
        'High': 'red',
        'Moderate to High': 'orange',
        'Moderate': 'yellow',
        'Low to Moderate': 'lightgreen',
        'Low': 'darkgreen'
    }

    risk_labels = {
        (1, 1): ('Low', 1), (1, 2): ('Low', 5), (1, 3): ('Low to Moderate', 10), (1, 4): ('Moderate', 15), (1, 5): ('High', 20),
        (2, 1): ('Low', 2), (2, 2): ('Low to Moderate', 6), (2, 3): ('Low to Moderate', 11), (2, 4): ('Moderate to High', 16), (2, 5): ('High', 21),
        (3, 1): ('Low', 3), (3, 2): ('Low to Moderate', 8), (3, 3): ('Moderate', 13), (3, 4): ('Moderate to High', 18), (3, 5): ('High', 23),
        (4, 1): ('Low', 4), (4, 2): ('Low to Moderate', 9), (4, 3): ('Moderate', 14), (4, 4): ('Moderate to High', 19), (4, 5): ('High', 24),
        (5, 1): ('Low to Moderate', 7), (5, 2): ('Moderate', 12), (5, 3): ('Moderate to High', 17), (5, 4): ('High', 22), (5, 5): ('High', 25)
    }

    # Siapkan warna untuk setiap cell
    for (y, x), (label, _) in risk_labels.items():
        color_matrix[y - 1][x - 1] = label_colors.get(label, 'white')

    # Masukkan nomor risiko ke dalam cell
    for _, row in df.iterrows():
        try:
            y = int(row["Skala Probabilitas Q1"]) - 1
            x = int(row["Skala Dampak Q1"]) - 1
            nomor = f"#{int(row['No'])}"
            if 0 <= x < 5 and 0 <= y < 5:
                existing = risk_matrix[y][x].replace("\n", ", ").split(", ") if risk_matrix[y][x] else []
                if nomor not in existing:
                    existing.append(nomor)
                lines = [", ".join(existing[k:k + 4]) for k in range(0, len(existing), 4)]
                risk_matrix[y][x] = "\n".join(lines)
        except Exception as e:
            st.warning(f"Gagal memproses baris: {e}")
            continue

    # Buat grafik
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
    ax.set_xlabel("Skala Dampak Q1")
    ax.set_ylabel("Skala Probabilitas Q1")
    ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)
    plt.tight_layout()

    st.pyplot(fig)

def tampilkan_heatmap_residual_q2():

    df = st.session_state.get("copy_tabel_residual_q1", pd.DataFrame())

    if df.empty:
        st.warning("⚠️ Tabel residual Q1 belum tersedia.")
        return

    # Cek kolom penting
    if "Skala Q2_Probabilitas" not in df.columns or "Skala Q2_Dampak" not in df.columns:
        st.error("❌ Kolom 'Skala Q2_Probabilitas' atau 'Skala Q2_Dampak' tidak ditemukan.")
        return
    if "No" not in df.columns:
        st.error("❌ Kolom 'No' tidak ditemukan untuk label risiko.")
        return

    df["No"] = pd.to_numeric(df["No"], errors="coerce").fillna(0).astype(int)

    st.subheader("Heatmap Matriks Risiko Residual Q2")

    # Inisialisasi matriks
    color_matrix = np.full((5, 5), 'white', dtype=object)
    risk_matrix = [['' for _ in range(5)] for _ in range(5)]

    # Mapping warna dan label risiko
    label_colors = {
        'High': 'red',
        'Moderate to High': 'orange',
        'Moderate': 'yellow',
        'Low to Moderate': 'lightgreen',
        'Low': 'darkgreen'
    }

    risk_labels = {
        (1, 1): ('Low', 1), (1, 2): ('Low', 5), (1, 3): ('Low to Moderate', 10), (1, 4): ('Moderate', 15), (1, 5): ('High', 20),
        (2, 1): ('Low', 2), (2, 2): ('Low to Moderate', 6), (2, 3): ('Low to Moderate', 11), (2, 4): ('Moderate to High', 16), (2, 5): ('High', 21),
        (3, 1): ('Low', 3), (3, 2): ('Low to Moderate', 8), (3, 3): ('Moderate', 13), (3, 4): ('Moderate to High', 18), (3, 5): ('High', 23),
        (4, 1): ('Low', 4), (4, 2): ('Low to Moderate', 9), (4, 3): ('Moderate', 14), (4, 4): ('Moderate to High', 19), (4, 5): ('High', 24),
        (5, 1): ('Low to Moderate', 7), (5, 2): ('Moderate', 12), (5, 3): ('Moderate to High', 17), (5, 4): ('High', 22), (5, 5): ('High', 25)
    }

    # Siapkan warna untuk setiap cell
    for (y, x), (label, _) in risk_labels.items():
        color_matrix[y - 1][x - 1] = label_colors.get(label, 'white')

    # Masukkan nomor risiko ke dalam cell
    for _, row in df.iterrows():
        try:
            y = int(row["Skala Q2_Probabilitas"]) - 1
            x = int(row["Skala Q2_Dampak"]) - 1
            nomor = f"#{int(row['No'])}"
            if 0 <= x < 5 and 0 <= y < 5:
                existing = risk_matrix[y][x].replace("\n", ", ").split(", ") if risk_matrix[y][x] else []
                if nomor not in existing:
                    existing.append(nomor)
                lines = [", ".join(existing[k:k + 4]) for k in range(0, len(existing), 4)]
                risk_matrix[y][x] = "\n".join(lines)
        except Exception as e:
            st.warning(f"Gagal memproses baris: {e}")
            continue

    # Buat grafik
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
    ax.set_xlabel("Skala Q2_Dampak")
    ax.set_ylabel("Skala 02 Probabilitas")
    ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)
    plt.tight_layout()

    st.pyplot(fig)
    
def tampilkan_heatmap_residual_q3():
    df = st.session_state.get("copy_tabel_residual_q1", pd.DataFrame())

    if df.empty:
        st.warning("⚠️ Tabel residual Q1 belum tersedia.")
        return

    if "Skala Q3_Probabilitas" not in df.columns or "Skala Q3_Dampak" not in df.columns:
        st.error("❌ Kolom 'Skala Q3_Probabilitas' atau 'Skala Q3_Dampak' tidak ditemukan.")
        return
    if "No" not in df.columns:
        st.error("❌ Kolom 'No' tidak ditemukan untuk label risiko.")
        return

    df["No"] = pd.to_numeric(df["No"], errors="coerce").fillna(0).astype(int)

    st.subheader("Heatmap Matriks Risiko Residual Q3")

    color_matrix = np.full((5, 5), 'white', dtype=object)
    risk_matrix = [['' for _ in range(5)] for _ in range(5)]

    label_colors = {
        'High': 'red',
        'Moderate to High': 'orange',
        'Moderate': 'yellow',
        'Low to Moderate': 'lightgreen',
        'Low': 'darkgreen'
    }

    risk_labels = {
        (1, 1): ('Low', 1), (1, 2): ('Low', 5), (1, 3): ('Low to Moderate', 10), (1, 4): ('Moderate', 15), (1, 5): ('High', 20),
        (2, 1): ('Low', 2), (2, 2): ('Low to Moderate', 6), (2, 3): ('Low to Moderate', 11), (2, 4): ('Moderate to High', 16), (2, 5): ('High', 21),
        (3, 1): ('Low', 3), (3, 2): ('Low to Moderate', 8), (3, 3): ('Moderate', 13), (3, 4): ('Moderate to High', 18), (3, 5): ('High', 23),
        (4, 1): ('Low', 4), (4, 2): ('Low to Moderate', 9), (4, 3): ('Moderate', 14), (4, 4): ('Moderate to High', 19), (4, 5): ('High', 24),
        (5, 1): ('Low to Moderate', 7), (5, 2): ('Moderate', 12), (5, 3): ('Moderate to High', 17), (5, 4): ('High', 22), (5, 5): ('High', 25)
    }

    for (y, x), (label, _) in risk_labels.items():
        color_matrix[y - 1][x - 1] = label_colors.get(label, 'white')

    for _, row in df.iterrows():
        try:
            y = int(row["Skala Q3_Probabilitas"]) - 1
            x = int(row["Skala Q3_Dampak"]) - 1
            nomor = f"#{int(row['No'])}"
            if 0 <= x < 5 and 0 <= y < 5:
                existing = risk_matrix[y][x].replace("\n", ", ").split(", ") if risk_matrix[y][x] else []
                if nomor not in existing:
                    existing.append(nomor)
                lines = [", ".join(existing[k:k + 4]) for k in range(0, len(existing), 4)]
                risk_matrix[y][x] = "\n".join(lines)
        except Exception as e:
            st.warning(f"Gagal memproses baris: {e}")
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
    ax.set_xlabel("Skala Q3_Dampak")
    ax.set_ylabel("Skala Q3 Probabilitas")
    ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)
    plt.tight_layout()

    st.pyplot(fig)

def tampilkan_heatmap_residual_q4():
    df = st.session_state.get("copy_tabel_residual_q1", pd.DataFrame())

    if df.empty:
        st.warning("⚠️ Tabel residual Q1 belum tersedia.")
        return

    if "Skala Q4_Probabilitas" not in df.columns or "Skala Q4_Dampak" not in df.columns:
        st.error("❌ Kolom 'Skala Q4_Probabilitas' atau 'Skala Q4_Dampak' tidak ditemukan.")
        return
    if "No" not in df.columns:
        st.error("❌ Kolom 'No' tidak ditemukan untuk label risiko.")
        return

    df["No"] = pd.to_numeric(df["No"], errors="coerce").fillna(0).astype(int)

    st.subheader("Heatmap Matriks Risiko Residual Q4")

    color_matrix = np.full((5, 5), 'white', dtype=object)
    risk_matrix = [['' for _ in range(5)] for _ in range(5)]

    label_colors = {
        'High': 'red',
        'Moderate to High': 'orange',
        'Moderate': 'yellow',
        'Low to Moderate': 'lightgreen',
        'Low': 'darkgreen'
    }

    risk_labels = {
        (1, 1): ('Low', 1), (1, 2): ('Low', 5), (1, 3): ('Low to Moderate', 10), (1, 4): ('Moderate', 15), (1, 5): ('High', 20),
        (2, 1): ('Low', 2), (2, 2): ('Low to Moderate', 6), (2, 3): ('Low to Moderate', 11), (2, 4): ('Moderate to High', 16), (2, 5): ('High', 21),
        (3, 1): ('Low', 3), (3, 2): ('Low to Moderate', 8), (3, 3): ('Moderate', 13), (3, 4): ('Moderate to High', 18), (3, 5): ('High', 23),
        (4, 1): ('Low', 4), (4, 2): ('Low to Moderate', 9), (4, 3): ('Moderate', 14), (4, 4): ('Moderate to High', 19), (4, 5): ('High', 24),
        (5, 1): ('Low to Moderate', 7), (5, 2): ('Moderate', 12), (5, 3): ('Moderate to High', 17), (5, 4): ('High', 22), (5, 5): ('High', 25)
    }

    for (y, x), (label, _) in risk_labels.items():
        color_matrix[y - 1][x - 1] = label_colors.get(label, 'white')

    for _, row in df.iterrows():
        try:
            y = int(row["Skala Q4_Probabilitas"]) - 1
            x = int(row["Skala Q4_Dampak"]) - 1
            nomor = f"#{int(row['No'])}"
            if 0 <= x < 5 and 0 <= y < 5:
                existing = risk_matrix[y][x].replace("\n", ", ").split(", ") if risk_matrix[y][x] else []
                if nomor not in existing:
                    existing.append(nomor)
                lines = [", ".join(existing[k:k + 4]) for k in range(0, len(existing), 4)]
                risk_matrix[y][x] = "\n".join(lines)
        except Exception as e:
            st.warning(f"Gagal memproses baris: {e}")
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
    ax.set_xlabel("Skala Q4_Dampak")
    ax.set_ylabel("Skala Q4 Probabilitas")
    ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)
    plt.tight_layout()

    st.pyplot(fig)

def main():
    st.title("📊 Heatmap Risiko (Inherent & Residual Q1–Q4)")

    init_session_state()
    load_file_inherent_residual()
    persist_updated_data()
    df_inherent = merge_tables()

    if not df_inherent.empty:
        if "No" not in df_inherent.columns:
            df_inherent["No"] = range(1, len(df_inherent) + 1)
        with st.expander("Tabel dan Heatmap Risiko Inherent", expanded=True):
            tampilkan_matriks_risiko(df=df_inherent)
            st.dataframe(df_inherent, use_container_width=True)
    else:
        st.warning("⚠️ Data risiko inherent belum tersedia.")

    if "copy_tabel_residual_q1" not in st.session_state or st.session_state["copy_tabel_residual_q1"].empty:
        gabungkan_residual_q1()

    df_residual = st.session_state["copy_tabel_residual_q1"]

    with st.expander("Tabel Gabungan Residual Q1"):
        if not df_residual.empty:
            tampilkan_heatmap_residual_q1()
            st.dataframe(df_residual, use_container_width=True)

    with st.expander("Tabel Gabungan Residual Q2"):
        if "Skala Q2_Dampak" in df_residual.columns:
            tampilkan_heatmap_residual_q2()
            st.dataframe(df_residual, use_container_width=True)

    with st.expander("Tabel Gabungan Residual Q3"):
        if "Skala Q3_Dampak" in df_residual.columns:
            tampilkan_heatmap_residual_q3()
            st.dataframe(df_residual, use_container_width=True)

    with st.expander("Tabel Gabungan Residual Q4"):
        if "Skala Q4_Dampak" in df_residual.columns:
            tampilkan_heatmap_residual_q4()
            st.dataframe(df_residual, use_container_width=True)
