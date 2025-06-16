import streamlit as st
import datetime
import re
import openai
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid import AgGrid
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image

def format_number_with_comma(number):
    return "{:,.0f}".format(number)

def get_project_inputs():
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("static/via_icon.jpg", width=200)

    with col2:
        st.markdown("""
        <div style='display: flex; flex-direction: column; justify-content: flex-start; align-items: flex-start; margin-top: -30px;'>
            <h1 style='font-size:30px; font-weight: bold; color: #333;'>RCSA Berbasis AI</h1>
            <p style='font-size: 18px; color: #666;'>Aplikasi Risk and Control Self-Assessment (RCSA) berbasis AI adalah sistem yang dirancang untuk mengidentifikasi, menilai, dan mengelola risiko serta efektivitas kontrol secara otomatis dan berbasis data.</p>
        </div>
        """, unsafe_allow_html=True)

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

    return project_description, project_goal, stakeholders, start_date, end_date, input_budget, input_limit_risiko
def process_and_validate_budget(input_budget, input_limit_risiko):
    import streamlit as st

    clean_budget = 0
    clean_limit_risiko = 0
    formatted_budget = ""
    formatted_limit_risiko = ""

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

    return clean_budget, clean_limit_risiko, formatted_budget, formatted_limit_risiko

def save_project_data(project_description, project_goal, stakeholders, start_date, end_date, clean_budget, clean_limit_risiko):
    import streamlit as st

    st.session_state.project_description = project_description
    st.session_state.project_goal = project_goal
    st.session_state.stakeholders = stakeholders
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    st.session_state.budget = clean_budget
    st.session_state.limit_risk = clean_limit_risiko

    st.success("Data berhasil disimpan!")
def display_project_recap():
    import streamlit as st

    if "project_description" in st.session_state:
        st.subheader("📋 Rekap Proyek")
        st.write(f"**📌 Deskripsi Proyek:**\n{st.session_state.project_description}")
        st.write(f"**🎯 Tujuan Proyek:**\n{st.session_state.project_goal}")
        st.write(f"**👥 Stakeholders:**\n{st.session_state.stakeholders}")
        st.write(f"**📅 Tanggal Mulai:** {st.session_state.start_date}")
        st.write(f"**📅 Tanggal Selesai:** {st.session_state.end_date}")
        st.write(f"**💰 Anggaran:** Rp {format_number_with_comma(st.session_state.budget)}")
        st.write(f"**⚠️ Limit Risiko:** Rp {format_number_with_comma(st.session_state.limit_risk)}")

def get_risk_suggestions(project_description, project_goal, stakeholders, start_date, end_date, project_budget, limit_risk):
    import openai

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
    8. Lingkungan
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for project risk assessment."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return response.choices[0].message['content']

def display_risk_suggestions():
    import streamlit as st

    if "gpt_response" in st.session_state:
        # Mengonversi respons GPT menjadi list risiko
        risk_list = st.session_state.gpt_response.split('\n')
        relevant_risks = [risk.strip() for risk in risk_list if risk.strip()]

        # Pindahkan pemilihan risiko ke sidebar
        with st.sidebar:
            selected_risks = []
            for risk in relevant_risks:
                if risk.endswith(':'):
                    st.markdown(f"**{risk}**")
                else:
                    checkbox = st.checkbox(risk)
                    if checkbox:
                        selected_risks.append(risk)

            # Simpan ke session_state
            st.session_state.selected_risks = selected_risks

def identify_and_calculate_risks():
    import streamlit as st
    import pandas as pd
    import numpy as np

    if "selected_risks" in st.session_state:
        st.subheader("3. Identifikasi Risiko")
        inherent_risks = {}
        risk_data = []
        risk_number = 1
        total_inherent_risk_exposure = 0
        limit_risk = st.session_state.limit_risk

        for risk in st.session_state.selected_risks:
            with st.expander(risk):
                impact = st.text_input(f"Masukkan Nilai Dampak untuk {risk}", '1,000,000,000', key=risk+"_impact")
                if impact:
                    clean_impact = float(impact.replace(",", ""))
                    formatted_impact = format_number_with_comma(clean_impact)

                    if clean_impact > 0.80 * limit_risk:
                        impact_scale = 5
                    elif 0.60 * limit_risk < clean_impact <= 0.80 * limit_risk:
                        impact_scale = 4
                    elif 0.40 * limit_risk < clean_impact <= 0.60 * limit_risk:
                        impact_scale = 3
                    elif 0.20 * limit_risk < clean_impact <= 0.40 * limit_risk:
                        impact_scale = 2
                    else:
                        impact_scale = 1

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
                    likelihood_value = likelihood_values[likelihood_labels.index(likelihood)]
                    likelihood_percentage = likelihood_value * 0.20

                    inherent_risk_exposure_value = clean_impact * likelihood_percentage
                    inherent_risks[risk] = {
                        "impact": formatted_impact,
                        "impact_scale": impact_scale,
                        "likelihood_percentage": likelihood_percentage * 100,
                        "inherent_risk_exposure": inherent_risk_exposure_value,
                    }

                    risk_data.append({
                        "No": risk_number,
                        "Risiko": risk,
                        "Dampak": formatted_impact,
                        "Skala Dampak": impact_scale,
                        "Skala Kemungkinan": likelihood_value,
                        "Kemungkinan (%)": likelihood_percentage * 100,
                        "Inherent Risk Exposure": format_number_with_comma(inherent_risk_exposure_value),
                    })

                    total_inherent_risk_exposure += inherent_risk_exposure_value
                    st.session_state["total_inherent_risk_exposure"] = total_inherent_risk_exposure
                    risk_number += 1

        if risk_data:
            st.subheader("4. Tabel Inherent Risk Exposure")
            risk_df = pd.DataFrame(risk_data)
            total_row = pd.DataFrame([{
                "No": "",
                "Risiko": "Total Inherent Risk Exposure",
                "Dampak": "",
                "Skala Dampak": "",
                "Skala Kemungkinan": "",
                "Kemungkinan (%)": "",
                "Inherent Risk Exposure": format_number_with_comma(total_inherent_risk_exposure),
            }])
            risk_df = pd.concat([risk_df, total_row], ignore_index=True)
            st.session_state["Tabel Inherent"] = risk_df.to_dict(orient="records")
            st.table(risk_data)
            st.write(f"Total Inherent Risk Exposure: {format_number_with_comma(total_inherent_risk_exposure)}")
def display_risk_matrix():
    import streamlit as st
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    if "Tabel Inherent" in st.session_state:
        st.subheader("5. Matriks Risiko Inherent")
        risk_df = pd.DataFrame(st.session_state["Tabel Inherent"]).dropna(subset=["Skala Dampak", "Skala Kemungkinan"])

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

        fig, ax = plt.subplots(figsize=(5, 3), dpi=150)
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
def edit_and_confirm_mitigations():
    import streamlit as st
    import pandas as pd
    import re

    if "selected_risks" in st.session_state:
        st.subheader("6. Edit & Konfirmasi Saran Mitigasi per Risiko")

        # Inisialisasi storage per risiko
        if "confirmed_mitigations_per_risk" not in st.session_state:
            st.session_state.confirmed_mitigations_per_risk = {}

        for risk in st.session_state.selected_risks:
            with st.expander(f"Risiko: {risk}"):
                if risk not in st.session_state:
                    if st.button(f"Peroleh Saran Mitigasi untuk {risk}"):
                        risk_handling_suggestions = get_risk_handling_suggestions(risk)
                        st.session_state[risk] = risk_handling_suggestions

                if risk in st.session_state:
                    risk_suggestion = st.session_state[risk]

                    # Parsing hasil GPT
                    mitigasi_list = re.findall(r"Mitigasi:\s*(.+)", risk_suggestion)
                    kpi_list = re.findall(r"KPI:\s*([^:]+)", risk_suggestion)
                    target_kpi_list = re.findall(r"Target KPI:\s*(\d+)", risk_suggestion)
                    pic_list = re.findall(r"PIC:\s*(.+)", risk_suggestion)
                    biaya_list = re.findall(r"Biaya:\s*(\d+)", risk_suggestion)
                    waktu_list = re.findall(r"Waktu Pelaksanaan:\s*(\d+)", risk_suggestion)

                    # Fallback jika mitigasi_list kosong
                    if not mitigasi_list and kpi_list:
                        mitigasi_list = [f"Mitigasi untuk: {risk}"] * len(kpi_list)

                    max_length = max(map(len, [mitigasi_list, kpi_list, target_kpi_list, pic_list, biaya_list, waktu_list]))
                    mitigasi_list += [""] * (max_length - len(mitigasi_list))
                    kpi_list += [""] * (max_length - len(kpi_list))
                    target_kpi_list += ["0"] * (max_length - len(target_kpi_list))
                    pic_list += ["Belum Ditentukan"] * (max_length - len(pic_list))
                    biaya_list += ["0"] * (max_length - len(biaya_list))
                    waktu_list += ["0"] * (max_length - len(waktu_list))

                    # Konversi angka
                    target_kpi_list = [int(x) for x in target_kpi_list]
                    biaya_list = [int(x) for x in biaya_list]
                    waktu_list = [int(x) for x in waktu_list]

                    # Buat DataFrame
                    mitigasi_df = pd.DataFrame({
                        "Program Mitigasi": mitigasi_list,
                        "KPI": kpi_list,
                        "Target KPI": target_kpi_list,
                        "PIC": pic_list,
                        "Biaya": biaya_list,
                        "Waktu Pelaksanaan": waktu_list
                    })

                    # Editor interaktif
                    edited_df = st.data_editor(mitigasi_df, use_container_width=True, hide_index=True, key=f"edited_{risk}")

                    if st.button(f"Konfirmasi Mitigasi untuk {risk}"):
                        st.session_state.confirmed_mitigations_per_risk[risk] = edited_df
                        st.success(f"Saran mitigasi untuk '{risk}' berhasil dikonfirmasi!")

        # Gabungkan semua mitigasi yang sudah dikonfirmasi
        all_mitigations = []
        for df in st.session_state.confirmed_mitigations_per_risk.values():
            all_mitigations.append(df)

        if all_mitigations:
            st.session_state.all_mitigations = pd.concat(all_mitigations, ignore_index=True)
            st.subheader("✅ Tabel Semua Mitigasi (Final)")
            st.data_editor(st.session_state.all_mitigations, use_container_width=True, hide_index=True, key="final_mitigations")
        else:
            st.info("Belum ada mitigasi yang dikonfirmasi.")



def edit_and_confirm_risks():
    import streamlit as st
    import pandas as pd

    if "gpt_response" in st.session_state:
        st.subheader("2. Edit & Konfirmasi Saran Risiko per Kategori")

        # Pisahkan baris
        lines = [line.strip() for line in st.session_state.gpt_response.split('\n') if line.strip()]
        current_category = None
        category_risks = {}

        for line in lines:
            if line.endswith(':'):
                current_category = line.rstrip(':')
                category_risks[current_category] = []
            else:
                if current_category:
                    category_risks[current_category].append(line)

        # Inisialisasi storage per kategori
        if "confirmed_risks_per_category" not in st.session_state:
            st.session_state.confirmed_risks_per_category = {}

        for category, risks in category_risks.items():
            with st.expander(f"Kategori: {category}"):
                df_risks = pd.DataFrame({"Risiko": risks})
                edited_df = st.data_editor(df_risks, use_container_width=True, hide_index=True, key=f"edited_{category}")

                if st.button(f"Konfirmasi Risiko untuk {category}"):
                    confirmed_risks = edited_df["Risiko"].fillna("").tolist()
                    confirmed_risks = [risk for risk in confirmed_risks if risk.strip()]
                    # Simpan di session_state
                    st.session_state.confirmed_risks_per_category[category] = confirmed_risks
                    st.success(f"{len(confirmed_risks)} risiko pada kategori '{category}' berhasil dikonfirmasi!")

        # Gabungkan semua risiko yang sudah dikonfirmasi
        all_confirmed_risks = []
        for risks in st.session_state.confirmed_risks_per_category.values():
            all_confirmed_risks.extend(risks)

        # Simpan final di session_state
        st.session_state.selected_risks = all_confirmed_risks

        if all_confirmed_risks:
            st.subheader("✅ Semua Risiko Terpilih (Final)")
            final_df = pd.DataFrame({"Risiko yang Dipilih": all_confirmed_risks})
            st.data_editor(final_df, use_container_width=True, hide_index=True, key="final_confirmed_risks")
        else:
            st.info("Belum ada risiko yang dikonfirmasi. Silakan gunakan tombol di setiap kategori.")
def get_risk_handling_suggestions(risk):
    import openai

    prompt = f"""
    Berikut adalah risiko yang terpilih: {risk}.
    Berikan 3 program mitigasi yang dapat diterapkan untuk mengurangi risiko ini, berikan hanya nama programnya saja (1 kalimat ringkas, misalnya 'Audit kontrak internal', 'Pelatihan kepatuhan'), dan rekomendasi untuk:
    - KPI (Indikator Kinerja)
    - Target KPI (Angka yang harus dicapai)
    - PIC (Penanggung Jawab)
    - Biaya (Estimasi biaya mitigasi dalam angka)
    - Waktu Pelaksanaan (Perkiraan waktu dalam bulan)

    Format jawaban:
    - Setiap nama program mitigasi harus dimulai dengan kata 'Program Mitigasi:'
    - Setiap KPI harus dimulai dengan kata 'KPI:'
    - Setiap Target KPI harus dimulai dengan kata 'Target KPI:' dan hanya berisi angka
    - Setiap PIC harus dimulai dengan kata 'PIC:'
    - Setiap Biaya harus dimulai dengan kata 'Biaya:' dan hanya berisi angka
    - Setiap Waktu Pelaksanaan harus dimulai dengan kata 'Waktu Pelaksanaan:' dan hanya berisi angka dalam bulan

    Contoh:
    Program Mitigasi: Pelatihan Kepatuhan Kontrak
    KPI: Tingkat kepatuhan kontrak - Target KPI
    Target KPI: 95
    PIC: Manajer Kontrak
    Biaya: 10000000
    Waktu Pelaksanaan: 6
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


    
    
def display_and_update_mitigations():
    import streamlit as st
    import pandas as pd
    import re

    if "all_mitigations" not in st.session_state:
        st.session_state["all_mitigations"] = pd.DataFrame(columns=["Program Mitigasi", "KPI", "Target KPI", "PIC", "Biaya", "Waktu Pelaksanaan"])

    if "selected_risks" in st.session_state:
        st.subheader("6. Detail Penanganan Risiko")

        with st.sidebar:
            for risk in st.session_state.selected_risks:
                if risk not in st.session_state:
                    if st.button(f"Peroleh Penanganan Risiko untuk {risk}"):
                        risk_handling_suggestions = get_risk_handling_suggestions(risk)
                        st.session_state[risk] = risk_handling_suggestions

        if "mitigations_list" not in st.session_state:
            st.session_state["mitigations_list"] = []

        mitigations_list = []

        for idx, risk in enumerate(st.session_state.get("selected_risks", []), start=1):
            if risk in st.session_state:
                risk_suggestion = st.session_state[risk]

                with st.expander(f"Detail Risiko #{idx}: {risk}"):
                    st.markdown(f"**Detail Risiko #{idx}: {risk}**")

                    mitigasi_list = re.findall(r"Program Mitigasi:\s*(.+)", risk_suggestion)

                    # Fallback jika kosong
                    if not mitigasi_list and kpi_list:
                        mitigasi_list = [f"Program Mitigasi untuk: {risk}"] * len(kpi_list)
                    kpi_list = re.findall(r"KPI:\s*([^:]+)", risk_suggestion)
                    target_kpi_list = re.findall(r"Target KPI:\s*(\d+)", risk_suggestion)
                    pic_list = re.findall(r"PIC:\s*(.+)", risk_suggestion)
                    biaya_list = re.findall(r"Biaya:\s*(\d+)", risk_suggestion)
                    waktu_list = re.findall(r"Waktu Pelaksanaan:\s*(\d+)", risk_suggestion)

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

                    edited_mitigasi_df = st.data_editor(program_mitigasi_df, use_container_width=True, hide_index=True, key=f"table_{idx}")
                    mitigations_list.append(edited_mitigasi_df)

        st.session_state["mitigations_list"] = mitigations_list

        if st.button("Update dan Gabungkan Semua Mitigasi"):
            if len(st.session_state["mitigations_list"]) > 0:
                st.session_state["all_mitigations"] = pd.concat(st.session_state["mitigations_list"], ignore_index=True)
                st.success("Semua mitigasi berhasil digabungkan!")
            else:
                st.warning("Tidak ada data mitigasi yang tersedia untuk digabungkan.")

        st.subheader("Tabel Semua Mitigasi")
        if not st.session_state["all_mitigations"].empty:
            updated_all_mitigations = st.data_editor(st.session_state["all_mitigations"], use_container_width=True, hide_index=True, key="all_mitigations_table")
        else:
            st.warning("Data mitigasi belum tersedia. Klik tombol untuk menggabungkan mitigasi.")
def update_monitoring_kpi():
    import streamlit as st
    import pandas as pd

    if "all_mitigations" not in st.session_state:
        st.session_state["all_mitigations"] = pd.DataFrame()
    if "update_all_mitigation" not in st.session_state:
        st.session_state["update_all_mitigation"] = pd.DataFrame()
    if "monitoring_kpi" not in st.session_state:
        st.session_state["monitoring_kpi"] = pd.DataFrame()

    if st.button("Update All Mitigation"):
        if not st.session_state["all_mitigations"].empty:
            st.session_state["update_all_mitigation"] = st.session_state["all_mitigations"]
            st.success("Data berhasil diperbarui ke 'update_all_mitigation'.")

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

    if not st.session_state["monitoring_kpi"].empty:
        st.subheader("Tabel Monitoring KPI")
        edited_kpi = st.data_editor(st.session_state["monitoring_kpi"], use_container_width=True, hide_index=True, key="monitoring_kpi_table")

        if st.button("Update Monitoring KPI"):
            st.session_state["update_monitoring_kpi"] = edited_kpi.copy()
            st.success("Data Monitoring KPI berhasil disalin ke 'update_monitoring_kpi'.")
    else:
        st.warning("Monitoring KPI belum tersedia. Klik tombol 'Update All Mitigation' untuk memperbarui.")

def format_number_with_comma(number):
    return "{:,.0f}".format(number)

def main():
    st.title("🧠 RCSA AI - Risk & Control Self-Assessment")

    # 🔹 Input Informasi Proyek
    st.header("1. Informasi Proyek")
    project_description, project_goal, stakeholders, start_date, end_date, input_budget, input_limit_risiko = get_project_inputs()

    # 🔹 Proses Anggaran dan Limit Risiko
    clean_budget, clean_limit_risiko, formatted_budget, formatted_limit_risiko = process_and_validate_budget(input_budget, input_limit_risiko)

    # 🔹 Tombol Simpan
    if st.button("💾 Simpan Informasi Proyek"):
        save_project_data(project_description, project_goal, stakeholders, start_date, end_date, clean_budget, clean_limit_risiko)

    # 🔹 Rekap Proyek
    display_project_recap()

if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
