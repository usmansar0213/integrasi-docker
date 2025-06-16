
import streamlit as st
import datetime
import re 

# ✅ Pastikan fungsi ini ada di awal kode
def format_number_with_comma(number):
    """Mengonversi angka ke format dengan koma sebagai pemisah ribuan."""
    return "{:,.2f}".format(number)

import streamlit as st
import openai
import pandas as pd
import datetime
from dotenv import load_dotenv
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from st_aggrid.grid_options_builder import GridOptionsBuilder  # Impor GridOptionsBuilder
from st_aggrid import AgGrid
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
openai.api_key = st.secrets["openai_api_key"]


import streamlit as st

# ========== Tambahkan CSS Kustom ==========
st.markdown("""
<style>
/* Tombol Umum */
div.stButton > button {
    background-color: #FF4B4B;
    color: white;
    font-size: 16px;
    font-weight: bold;
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
    transition: 0.3s;
}
div.stButton > button:hover {
    background-color: #D62828;
    color: white;
}

/* Ukuran font dan layout global */
body {
    font-size: 20px;
}
h1 {
    font-size: 36px;
}
h2 {
    font-size: 30px;
}
h3 {
    font-size: 24px;
}
p {
    font-size: 20px;
}
.stDataFrame table, .stTable, .stText {
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# ========== Fungsi Utama ==========
def main():
    st.title("Risk and Control Self-Assessment (RCSA)")
    st.write("This is the RCSA module.")
    # Tambahkan logika RCSA lengkap Anda di sini

st.markdown("""
    <style>
    body {
        font-size: 20px;  /* Ukuran font untuk body */
    }
    h1 {
        font-size: 36px;  /* Ukuran font untuk judul utama */
    }
    h2 {
        font-size: 30px;  /* Ukuran font untuk subjudul */
    }
    h3 {
        font-size: 24px;  /* Ukuran font untuk heading kecil */
    }
    p {
        font-size: 20px;  /* Ukuran font untuk teks biasa */
    }
    /* Maksimalkan lebar semua elemen */
    .stDataFrame table, .stTable, .stText {
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)



# 2️⃣ Fungsi OpenAI Chat Completion
def chat_with_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a helpful AI assistant."},
                      {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response["choices"][0]["message"]["content"].strip()
    except openai.error.OpenAIError as e:
        print(f"Terjadi kesalahan pada OpenAI API: {e}")
        return "Error: Tidak dapat memproses permintaan."
        

# Langkah 1: Input Deskripsi Proyek dan Tujuan
col1, col2 = st.columns([1, 3])
with col1:
    st.image("Via_aviation.webp", width=200)

with col2:
    st.markdown("""
    <div style='display: flex; flex-direction: column; justify-content: flex-start; align-items: flex-start; margin-top: -30px;'>
        <h1 style='font-size:30px; font-weight: bold; color: #333;'>RCSA Berbasis AI</h1>
        <p style='font-size: 18px; color: #666;'>Aplikasi Risk and Control Self-Assessment (RCSA) berbasis AI adalah sistem yang dirancang untuk mengidentifikasi, menilai, dan mengelola risiko serta efektivitas kontrol secara otomatis dan berbasis data.</p>
    </div>
    """, unsafe_allow_html=True)

# Input Deskripsi Proyek
# Judul dan Deskripsi Aplikasi
  
project_description = st.text_area('Deskripsikan proyek Anda', 
    'Perawatan dan Manajemen Risiko Pesawat Kargo Internasional.\n'
    'Perjanjian penyediaan jasa perawatan pesawat antara PT. AviaTech dan Maskapai Kargo Internasional.\n'
    'PT. AviaTech bertanggung jawab untuk melakukan perawatan berkala, inspeksi keselamatan, dan perbaikan teknis pesawat.\n'
    'Proyek ini mencakup perawatan berkala setiap 6 bulan, pengecekan sistem navigasi setiap 3 bulan, dan manajemen risiko operasional.')

project_goal = st.text_area('Apa tujuan dari proyek Anda?', 
    '1. Memastikan pesawat beroperasi dengan aman dan efisien.\n'
    '2. Mengurangi downtime pesawat akibat perawatan dengan perencanaan berbasis AI.\n'
    '3. Meminimalkan risiko kegagalan mesin dan sistem avionik.\n'
    '4. Meningkatkan kepatuhan terhadap regulasi keselamatan penerbangan internasional.')

stakeholders = st.text_area('Siapa saja stakeholder yang terlibat?', 
    '- PT. AviaTech (Penyedia Jasa - MRO)\n'
    '- Maskapai Kargo Internasional (Pengguna Jasa)\n'
    '- Regulator Penerbangan (FAA, EASA, Kemenhub)\n'
    '- Perusahaan Asuransi Penerbangan\n'
    '- Penyedia Suku Cadang (Airbus, Boeing)')

start_date = st.date_input('Tanggal Mulai', value=datetime.date(2025, 4, 1))
end_date = st.date_input('Tanggal Selesai', min_value=start_date, value=start_date + datetime.timedelta(days=270))


input_budget = st.text_input('Berapa anggaran untuk proyek ini?', '75,000,000,000.00')
input_limit_risiko = st.text_input('Berapa Limit Risiko untuk proyek ini?', '5,000,000,000.00')


clean_budget = 0
clean_limit_risiko = 0

if input_budget:
    try:
        clean_budget = float(input_budget.replace(",", ""))
        formatted_budget = format_number_with_comma(clean_budget)
        st.session_state.budget = clean_budget
    except ValueError:
        st.error("Format anggaran salah. Masukkan angka valid dengan koma sebagai pemisah ribuan.")

if input_limit_risiko:
    try:
        clean_limit_risiko = float(input_limit_risiko.replace(",", ""))
        formatted_limit_risiko = format_number_with_comma(clean_limit_risiko)
        st.session_state.limit_risk = clean_limit_risiko
    except ValueError:
        st.error("Format limit risiko salah. Masukkan angka valid dengan koma sebagai pemisah ribuan.")

if st.button('Proses'):
   
    st.session_state.project_description = project_description
    st.session_state.project_goal = project_goal
    st.session_state.stakeholders = stakeholders
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    st.session_state.budget = clean_budget
    st.session_state.limit_risk = clean_limit_risiko

    st.success("Data berhasil disimpan!")


if "project_description" in st.session_state:
    st.subheader("📋 Rekap Proyek")
    st.write(f"**📌 Deskripsi Proyek:**\n{st.session_state.project_description}")
    st.write(f"**🎯 Tujuan Proyek:**\n{st.session_state.project_goal}")
    st.write(f"**👥 Stakeholders:**\n{st.session_state.stakeholders}")
    st.write(f"**📅 Tanggal Mulai:** {st.session_state.start_date}")
    st.write(f"**📅 Tanggal Selesai:** {st.session_state.end_date}")
    st.write(f"**💰 Anggaran:** Rp {format_number_with_comma(st.session_state.budget)}")
    st.write(f"**⚠️ Limit Risiko:** Rp {format_number_with_comma(st.session_state.limit_risk)}")
    
    
    
    st.subheader("2. Daftar Risiko Dari AI")


# Langkah 2: Mengirim Deskripsi ke GPT untuk Saran Risiko
def get_risk_suggestions(project_description, project_goal, stakeholders, start_date, end_date, project_budget, limit_risk):
    prompt = f"""
    Berikut deskripsi proyek, tujuan, stakeholder, tanggal mulai, tanggal selesai, anggaran, dan limit risiko:
    Deskripsi: {project_description}
    Tujuan: {project_goal}
    Stakeholders: {stakeholders}
    Tanggal Mulai: {start_date}
    Tanggal Selesai: {end_date}
    Anggaran: {project_budget}
    Limit Risiko: {limit_risk}
    
    Silakan berikan saran risiko yang mungkin terjadi dalam proyek ini terkait dengan kategori berikut:
    1. Kontraktual
    2. Keuangan & Pembayaran
    3. Komersial
    4. Operasi
    5. Teknik
    6. Hukum
    7. Reputasi
    8.. Lingkungan
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  
        messages=[{"role": "system", "content": "You are a helpful assistant for project risk assessment."},
                  {"role": "user", "content": prompt}],
        max_tokens=500  
    )
    return response.choices[0].message['content']

# Tombol untuk mendapatkan saran risiko
if st.button('Dapatkan Saran Risiko'):
    suggestion = get_risk_suggestions(
        project_description, 
        project_goal, 
        stakeholders, 
        start_date, 
        end_date, 
        formatted_budget, 
        formatted_limit_risiko
    )
    
    # Menyimpan respons GPT ke dalam session state
    st.session_state.gpt_response = suggestion
    st.write("Saran risiko telah disimpan, silakan pilih risiko yang relevan.")
    
    
    # Menambahkan dan mengonversi respons GPT menjadi list untuk checkbox
if 'gpt_response' in st.session_state:
    # Mengonversi respons GPT menjadi list risiko
    risk_list = st.session_state.gpt_response.split('\n')
    
    # Menyaring hanya risiko yang relevan
    relevant_risks = [risk.strip() for risk in risk_list if risk.strip()]
    
    # Pindahkan pemilihan risiko ke sidebar
    with st.sidebar:
               
        selected_risks = []
        for risk in relevant_risks:
            if risk.endswith(':'):
                # Menampilkan kategori risiko dengan format bold
                st.markdown(f"**{risk}**")
            else:
                # Menampilkan checkbox untuk memilih risiko
                checkbox = st.checkbox(risk)
                if checkbox:
                    selected_risks.append(risk)
        
        # Menyimpan selected_risks ke dalam session state untuk digunakan di langkah berikutnya
        st.session_state.selected_risks = selected_risks

# Langkah 2.2: Menambahkan Risiko Baru oleh Pengguna dan Menggabungkan dengan Risiko yang Terpilih
if 'selected_risks' in st.session_state:
    with st.sidebar:
        st.subheader("Tambah Risiko Baru")
        
        # Input untuk menambah beberapa risiko
        new_risk_names = st.text_area("Masukkan Nama Risiko Baru (pisahkan dengan koma atau baris baru)", "")
        if new_risk_names:
            # Mengonversi risiko yang dimasukkan pengguna menjadi daftar risiko yang terpisah per baris atau koma
            new_risks = [risk.strip() for risk in new_risk_names.replace(",", "\n").split("\n") if risk.strip()]
            # Menambahkan risiko baru ke dalam session state jika belum ada
            added_risks = []  # List untuk menyimpan risiko yang berhasil ditambahkan
            for new_risk in new_risks:
                if new_risk not in st.session_state.selected_risks:
                    st.session_state.selected_risks.append(new_risk)  # Menambahkan risiko baru ke dalam list risiko
                    added_risks.append(new_risk)  # Menyimpan risiko yang berhasil ditambahkan
            if added_risks:
                st.write(f"Risiko baru berhasil ditambahkan: {', '.join(added_risks)}")

from st_aggrid import AgGrid, GridOptionsBuilder


if 'selected_risks' in st.session_state:
    st.subheader("3. Identifikasi Risiko")

    inherent_risks = {}  # Initialize the dictionary to store inherent risks

    risk_data = []  # Initialize list to store risk data for the table
    risk_number = 1  # Inisialisasi nomor urut risiko
    total_inherent_risk_exposure = 0  # Inisialisasi total inherent risk exposure
    
    
    # Assume limit_risk is defined somewhere or is an input
    limit_risk = st.session_state.limit_risk  # Example limit for the sake of illustration

    for risk in st.session_state.selected_risks:
        with st.expander(risk):
            # Input Nilai Dampak dengan format otomatis
            impact = st.text_input(f"Masukkan Nilai Dampak untuk {risk}", '1,000,000,000', key=risk+"_impact")

            # Mengonversi input menjadi angka (float) setelah menghapus koma dan kemudian format ulang dengan koma
            if impact:
                clean_impact = float(impact.replace(",", ""))
                formatted_impact = format_number_with_comma(clean_impact)

            # Menentukan Skala Dampak berdasarkan perbandingan dengan Limit Risiko
            if clean_impact > 0.80 * limit_risk:
                impact_scale = 5
            elif 0.60 * limit_risk < clean_impact <= 0.80 * limit_risk:
                impact_scale = 4
            elif 0.40 * limit_risk < clean_impact <= 0.60 * limit_risk:
                impact_scale = 3
            elif 0.20 * limit_risk < clean_impact <= 0.40 * limit_risk:
                impact_scale = 2
            else:  # 0 <= clean_impact <= 0.20 * limit_risk
                impact_scale = 1

            # Input Skala Kemungkinan dengan referensi langsung di dalam opsi
            likelihood_options = {
                1: "1 - Sangat rendah (< 20%)",
                2: "2 - Rendah (20% - 40%)",
                3: "3 - Sedang (40% - 60%)",
                4: "4 - Tinggi (60% - 80%)",
                5: "5 - Sangat tinggi (> 80%)"
            }
            likelihood_labels = list(likelihood_options.values())
            likelihood_values = list(likelihood_options.keys())
            likelihood = st.selectbox(f"Masukkan Skala Kemungkinan untuk {risk}", likelihood_labels, index=2)

            # Konversi Skala Kemungkinan menjadi nilai numerik dan persentase
            likelihood_value = likelihood_values[likelihood_labels.index(likelihood)]
            likelihood_percentage = likelihood_value * 0.20

            # Menghitung Inherent Risk Exposure
            inherent_risk_exposure_value = clean_impact * likelihood_percentage
            inherent_risks[risk] = {
                "impact": formatted_impact,
                "impact_scale": impact_scale,
                "likelihood_percentage": likelihood_percentage * 100,  # Menampilkan dalam persen
                "inherent_risk_exposure": inherent_risk_exposure_value,
            }
            
            # Menyimpan data risiko dalam format dictionary untuk tabel
            risk_data.append({
                "No": risk_number,
                "Risiko": risk,
                "Dampak": formatted_impact,
                "Skala Dampak": impact_scale,
                "Skala Kemungkinan": likelihood_value,
                "Kemungkinan (%)": likelihood_percentage * 100,
                "Inherent Risk Exposure": format_number_with_comma(inherent_risk_exposure_value),
            })

            # Menambahkan nilai exposure ke total
            total_inherent_risk_exposure += inherent_risk_exposure_value
            
            st.session_state["total_inherent_risk_exposure"] = total_inherent_risk_exposure
            
            # Increment nomor urut risiko
            risk_number += 1


  
    # 4. Tabel Inherent Risk Exposure
    st.subheader("4. Tabel Inherent Risk Exposure")
    if risk_data:

        # Convert the risk data to a pandas DataFrame
        risk_df = pd.DataFrame(risk_data)

        # Menambahkan baris untuk Total Inherent Risk Exposure
        total_row = pd.DataFrame([{
            "No": "",  # Kosongkan No untuk baris total
            "Risiko": "Total Inherent Risk Exposure",  # Label total
            "Dampak": "",
            "Skala Dampak": "",
            "Skala Kemungkinan": "",
            "Kemungkinan (%)": "",
            "Inherent Risk Exposure": format_number_with_comma(total_inherent_risk_exposure),  # Total exposure
        }])

        # Menggabungkan baris total ke dalam DataFrame
        risk_df = pd.concat([risk_df, total_row], ignore_index=True)

        # Simpan ke session state dengan key "Tabel Inherent"
        st.session_state["Tabel Inherent"] = risk_df.to_dict(orient="records")

    st.table(risk_data)
    st.write(f"Total Inherent Risk Exposure: {format_number_with_comma(total_inherent_risk_exposure)}")


#Langkah 5: Matriks Risiko Inherent
    st.subheader("5. Matriks Risiko Inherent")
  
    # Mendefinisikan label risiko berdasarkan koordinat (Skala Kemungkinan, Skala Dampak)
    risk_labels = {
        (1, 1): ('Low', 1),
        (1, 2): ('Low', 5),
        (1, 3): ('Low to Moderate', 10),
        (1, 4): ('Moderate', 15),
        (1, 5): ('High', 20),
        (2, 1): ('Low', 2),
        (2, 2): ('Low to Moderate', 6),
        (2, 3): ('Low to Moderate', 11),
        (2, 4): ('Moderate to High', 16),
        (2, 5): ('High', 21),
        (3, 1): ('Low', 3),
        (3, 2): ('Low to Moderate', 8),
        (3, 3): ('Moderate', 13),
        (3, 4): ('Moderate to High', 18),
        (3, 5): ('High', 23),
        (4, 1): ('Low', 4),
        (4, 2): ('Low to Moderate', 9),
        (4, 3): ('Moderate', 14),
        (4, 4): ('Moderate to High', 19),
        (4, 5): ('High', 24),
        (5, 1): ('Low to Moderate', 7),
        (5, 2): ('Moderate', 12),
        (5, 3): ('Moderate to High', 17),
        (5, 4): ('High', 22),
        (5, 5): ('High', 25)
    }

    # Matriks risiko (5x5) dengan default warna dan label
    color_matrix = np.full((5, 5), 'white', dtype=object)
    risk_matrix = [['' for _ in range(5)] for _ in range(5)]

    # Menentukan warna berdasarkan label risiko
    for coord, (label, _) in risk_labels.items():
        if label == 'High':
            color_matrix[coord[0] - 1][coord[1] - 1] = 'red'
        elif label == 'Moderate to High':
            color_matrix[coord[0] - 1][coord[1] - 1] = 'orange'
        elif label == 'Moderate':
            color_matrix[coord[0] - 1][coord[1] - 1] = 'yellow'
        elif label == 'Low to Moderate':
            color_matrix[coord[0] - 1][coord[1] - 1] = 'lightgreen'
        elif label == 'Low':
            color_matrix[coord[0] - 1][coord[1] - 1] = 'darkgreen'

    # Memetakan nomor risiko ke matriks berdasarkan Skala Dampak dan Kemungkinan
    for index, row in risk_df.iterrows():
        try:
            skala_dampak = int(row['Skala Dampak'])
            skala_kemungkinan = int(row['Skala Kemungkinan'])
            nomor_risiko = f"#{row['No']}"
            if 1 <= skala_kemungkinan <= 5 and 1 <= skala_dampak <= 5:
                if risk_matrix[skala_kemungkinan - 1][skala_dampak - 1]:
                    risk_matrix[skala_kemungkinan - 1][skala_dampak - 1] += f", {nomor_risiko}"
                else:
                    risk_matrix[skala_kemungkinan - 1][skala_dampak - 1] = nomor_risiko
        except ValueError:
            continue

    # Membuat figur untuk matriks risiko
    fig, ax = plt.subplots(figsize=(5, 3), dpi=150)

    # Menampilkan matriks dengan warna dan nomor risiko
    for i in range(5):
        for j in range(5):
            ax.add_patch(plt.Rectangle((j, i), 1, 1, color=color_matrix[i, j], edgecolor='black', linewidth=0.5))
            label, number = risk_labels.get((i + 1, j + 1), ('', ''))
            ax.text(j + 0.5, i + 0.7, label, ha='center', va='center', fontsize=5, color='black')
            ax.text(j + 0.5, i + 0.5, str(number), ha='center', va='center', fontsize=5, color='black')
            ax.text(j + 0.5, i + 0.3, risk_matrix[i][j], ha='center', va='center', fontsize=5, color='blue')

    ax.set_xlim(0, 5)
    ax.set_ylim(0, 5)
    ax.set_xticks(np.arange(5) + 0.5)
    ax.set_yticks(np.arange(5) + 0.5)
    ax.set_xticklabels([1, 2, 3, 4, 5], fontsize=5)
    ax.set_yticklabels([1, 2, 3, 4, 5], fontsize=5)
    ax.set_xlabel("Skala Dampak", fontsize=10)
    ax.set_ylabel("Skala Kemungkinan", fontsize=10)
    ax.set_xticks(np.arange(0, 6, 1), minor=True)
    ax.set_yticks(np.arange(0, 6, 1), minor=True)
    ax.grid(which='minor', color='black', linestyle='-', linewidth=0.5)
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    st.pyplot(fig)

# Fungsi untuk mendapatkan saran dari GPT dengan tambahan rekomendasi untuk KPI, Target KPI, PIC, Biaya, dan Waktu Pelaksanaan
def get_risk_handling_suggestions(risk):
    prompt = f"""
    Berikut adalah risiko yang terpilih: {risk}.
    Berikan 3 program mitigasi yang dapat diterapkan untuk mengurangi risiko ini, serta rekomendasi untuk:
    - KPI (Indikator Kinerja)
    - Target KPI (Angka yang harus dicapai)
    - PIC (Penanggung Jawab)
    - Biaya (Estimasi biaya mitigasi dalam angka)
    - Waktu Pelaksanaan (Perkiraan waktu dalam bulan)

    Format jawaban:
    - Setiap mitigasi harus dimulai dengan kata "Mitigasi:"
    - Setiap KPI harus dimulai dengan kata "KPI:"
    - Setiap Target KPI harus dimulai dengan kata "Target KPI:" dan hanya berisi angka
    - Setiap PIC harus dimulai dengan kata "PIC:"
    - Setiap Biaya harus dimulai dengan kata "Biaya:" dan hanya berisi angka
    - Setiap Waktu Pelaksanaan harus dimulai dengan kata "Waktu Pelaksanaan:" dan hanya berisi angka dalam bulan

    Contoh:
    Mitigasi: Meningkatkan sistem pemantauan real-time untuk mengurangi potensi risiko.
    KPI: Waktu respons terhadap kejadian risiko dalam menit.
    Target KPI: 5
    PIC: Tim Keamanan IT
    Biaya: 50000000
    Waktu Pelaksanaan: 6

    Mitigasi: Melakukan pelatihan rutin bagi karyawan dalam mengelola risiko ini.
    KPI: Jumlah jam pelatihan yang telah diselesaikan per karyawan per tahun.
    Target KPI: 20
    PIC: Departemen HR
    Biaya: 25000000
    Waktu Pelaksanaan: 3
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  
        messages=[
            {"role": "system", "content": "You are a helpful assistant for risk management."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    
    return response.choices[0].message['content']

# Inisialisasi session state untuk menyimpan semua mitigasi yang telah diperbarui
if "all_mitigations" not in st.session_state:
    st.session_state["all_mitigations"] = pd.DataFrame(columns=["Program Mitigasi", "KPI", "Target KPI", "PIC", "Biaya", "Waktu Pelaksanaan"])

if 'selected_risks' in st.session_state:
    st.subheader("6. Detail Penanganan Risiko")

    # Menampilkan tombol di sidebar
    with st.sidebar:
        for risk in st.session_state.selected_risks:
            if risk not in st.session_state:
                if st.button(f"Peroleh Penanganan Risiko untuk {risk}"):
                    risk_handling_suggestions = get_risk_handling_suggestions(risk)
                    st.session_state[risk] = risk_handling_suggestions

    # List untuk menggabungkan semua mitigasi
    
    # Pastikan session state ada
    if "mitigations_list" not in st.session_state:
        st.session_state["mitigations_list"] = []

    if "all_mitigations" not in st.session_state:
        st.session_state["all_mitigations"] = pd.DataFrame()

    if "update_all_mitigation" not in st.session_state:
        st.session_state["update_all_mitigation"] = pd.DataFrame()

    # List untuk menyimpan mitigasi
    mitigations_list = []

    for idx, risk in enumerate(st.session_state.get("selected_risks", []), start=1):
        if risk in st.session_state:
            risk_suggestion = st.session_state[risk]
            
            with st.expander(f"Detail Risiko #{idx}: {risk}"):
                st.markdown(f"**Detail Risiko #{idx}: {risk}**")

                # Parsing hasil GPT
                mitigasi_list = re.findall(r"Mitigasi:\s*(.+)", risk_suggestion)
                kpi_list = re.findall(r"KPI:\s*([^:]+)", risk_suggestion)
                target_kpi_list = re.findall(r"Target KPI:\s*(\d+)", risk_suggestion)
                pic_list = re.findall(r"PIC:\s*(.+)", risk_suggestion)
                biaya_list = re.findall(r"Biaya:\s*(\d+)", risk_suggestion)
                waktu_list = re.findall(r"Waktu Pelaksanaan:\s*(\d+)", risk_suggestion)

                # Normalisasi panjang list
                max_length = max(map(len, [mitigasi_list, kpi_list, target_kpi_list, pic_list, biaya_list, waktu_list]))
                mitigasi_list += [""] * (max_length - len(mitigasi_list))
                kpi_list += [""] * (max_length - len(kpi_list))
                target_kpi_list += ["0"] * (max_length - len(target_kpi_list))
                pic_list += ["Belum Ditentukan"] * (max_length - len(pic_list))
                biaya_list += ["0"] * (max_length - len(biaya_list))
                waktu_list += ["0"] * (max_length - len(waktu_list))

                target_kpi_list = [int(x) for x in target_kpi_list]
                biaya_list = [int(x) for x in biaya_list]
                waktu_list = [int(x) for x in waktu_list]

                program_mitigasi_df = pd.DataFrame({
                    "Program Mitigasi": mitigasi_list,
                    "KPI": kpi_list,
                    "Target KPI": target_kpi_list,
                    "PIC": pic_list,
                    "Biaya": biaya_list,
                    "Waktu Pelaksanaan": waktu_list
                })

                # **Menggunakan key unik agar setiap tabel bisa diedit**
                edited_mitigasi_df = st.data_editor(program_mitigasi_df, use_container_width=True, hide_index=True, key=f"table_{idx}")

                # Simpan hasil edit ke list
                mitigations_list.append(edited_mitigasi_df)

    # **Simpan hasil edit ke session state**
    st.session_state["mitigations_list"] = mitigations_list

    # **Tombol untuk menggabungkan semua data mitigasi**
    if st.button("Update dan Gabungkan Semua Mitigasi"):
        if len(st.session_state["mitigations_list"]) > 0:
            st.session_state["all_mitigations"] = pd.concat(st.session_state["mitigations_list"], ignore_index=True)
            st.success("Semua mitigasi berhasil digabungkan!")
        else:
            st.warning("Tidak ada data mitigasi yang tersedia untuk digabungkan.")

    # **Menampilkan tabel semua mitigasi**
    st.subheader("Tabel Semua Mitigasi")
    if not st.session_state["all_mitigations"].empty:
        updated_all_mitigations = st.data_editor(st.session_state["all_mitigations"], use_container_width=True, hide_index=True, key="all_mitigations_table")
    else:
        st.warning("Data mitigasi belum tersedia. Klik tombol untuk menggabungkan mitigasi.")

    # Inisialisasi session state jika belum ada
    if "all_mitigations" not in st.session_state:
        st.session_state["all_mitigations"] = pd.DataFrame()

    if "update_all_mitigation" not in st.session_state:
        st.session_state["update_all_mitigation"] = pd.DataFrame()

    if "monitoring_kpi" not in st.session_state:
        st.session_state["monitoring_kpi"] = pd.DataFrame()

    # **Tombol untuk update All Mitigation**
    if st.button("Update All Mitigation"):
        if not st.session_state["all_mitigations"].empty:
            st.session_state["update_all_mitigation"] = st.session_state["all_mitigations"]
            st.success("Data berhasil diperbarui ke 'update_all_mitigation'.")

            # Langsung update Monitoring KPI setelah tombol ditekan
            if "Program Mitigasi" in st.session_state["all_mitigations"].columns:
                st.session_state["monitoring_kpi"] = pd.DataFrame({
                    "Mitigasi Risiko": st.session_state["all_mitigations"]["Program Mitigasi"].tolist(),
                    "KPI Triwulan 1": ["" for _ in range(len(st.session_state["all_mitigations"]))],
                    "KPI Triwulan 2": ["" for _ in range(len(st.session_state["all_mitigations"]))],
                    "KPI Triwulan 3": ["" for _ in range(len(st.session_state["all_mitigations"]))],
                    "KPI Triwulan 4": ["" for _ in range(len(st.session_state["all_mitigations"]))],
                })
                
        else:
            st.error("Tidak ada data mitigasi yang tersedia untuk diperbarui.")

    # **Menampilkan tabel Monitoring KPI jika sudah tersedia**
   
    if not st.session_state["monitoring_kpi"].empty:
        st.subheader("Tabel Monitoring KPI")
        edited_kpi = st.data_editor(st.session_state["monitoring_kpi"], use_container_width=True, hide_index=True, key="monitoring_kpi_table")

        # **Tombol Update Monitoring KPI di bawah tabel**
        if st.button("Update Monitoring KPI"):
            st.session_state["update_monitoring_kpi"] = edited_kpi.copy()
            st.success("Data Monitoring KPI berhasil disalin ke 'update_monitoring_kpi'.")

    else:
        st.warning("Monitoring KPI belum tersedia. Klik tombol 'Update All Mitigation' untuk memperbarui.")

    def save_to_png():
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', dpi=150)
        img_buffer.seek(0)
        return img_buffer

    
    def save_to_excel(session_data):
        """Fungsi untuk menyimpan data sesi ke dalam format Excel, termasuk gambar matriks risiko di sheet ke-5."""
        output = BytesIO()
        img_buffer = save_to_png()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet 1: Rekap Proyek
            rekap_df = pd.DataFrame({
                "Kategori": [
                    "Deskripsi Proyek",
                    "Tujuan Proyek",
                    "Stakeholders",
                    "Tanggal Mulai",
                    "Tanggal Selesai",
                    "Anggaran",
                    "Limit Risiko"
                ],
                "Detail": [
                    session_data.get("project_description", "N/A"),
                    session_data.get("project_goal", "N/A"),
                    session_data.get("stakeholders", "N/A"),
                    session_data.get("start_date", "N/A"),
                    session_data.get("end_date", "N/A"),
                    f"Rp {session_data.get('budget', 0):,.2f}",
                    f"Rp {session_data.get('limit_risk', 0):,.2f}"
                ]
            })
            rekap_df.to_excel(writer, sheet_name='Rekap Project', index=False)
            
            # Sheet 2: Risk Inherent
            risk_inherent = session_data.get("Tabel Inherent", [])
            pd.DataFrame(risk_inherent).to_excel(writer, sheet_name='Risk Inherent', index=False)

            # Sheet 3: All Mitigation
            all_mitigation = session_data.get("update_all_mitigation", [])
            pd.DataFrame(all_mitigation).to_excel(writer, sheet_name='All Mitigation', index=False)

            # Sheet 4: Monitoring KPI
            monitoring_kpi = session_data.get("update_monitoring_kpi", [])
            pd.DataFrame(monitoring_kpi).to_excel(writer, sheet_name='Monitoring KPI', index=False)

            # Sheet 5: Risk Matrix Image
            workbook = writer.book
            worksheet = workbook.add_worksheet("Risk Matrix Image")
            writer.sheets["Risk Matrix Image"] = worksheet
            worksheet.insert_image("B2", "risk_matrix.png", {'image_data': img_buffer})
        
        output.seek(0)
        return output

    # Tombol untuk menyimpan ke Excel
    st.title("Save Session Data to Excel")

    if st.button("Save to Excel with Risk Matrix Image"):
        excel_file = save_to_excel(st.session_state)
        st.download_button(label="Download Excel", data=excel_file, file_name="session_data_with_risk_matrix.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        

if __name__ == "__main__":
    main()
