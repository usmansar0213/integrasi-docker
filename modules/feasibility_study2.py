import streamlit as st
import datetime
import re
import openai
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid import AgGrid
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
def format_number_with_comma(number):
    return "{:,.2f}".format(number)

def setup_streamlit_styles():
    st.markdown("""
    <style>
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
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    body { font-size: 20px; }
    h1 { font-size: 36px; }
    h2 { font-size: 30px; }
    h3 { font-size: 24px; }
    p { font-size: 20px; }
    .stDataFrame table, .stTable, .stText { width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)
def get_project_inputs():
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("static/via_icon.jpg", width=200)

    with col2:
        st.markdown("""
        <div style='display: flex; flex-direction: column; justify-content: flex-start; align-items: flex-start; margin-top: -30px;'>
            <h1 style='font-size:30px; font-weight: bold; color: #333;'>RCSA Berbasis AI</h1>
            <p style='font-size: 18px; color: #666;'>Aplikasi Risk and Control Self-Assessment (RCSA) berbasis AI...</p>
        </div>
        """, unsafe_allow_html=True)

    project_description = st.text_area('Deskripsikan proyek Anda', '...')
    project_goal = st.text_area('Apa tujuan dari proyek Anda?', '...')
    stakeholders = st.text_area('Siapa saja stakeholder yang terlibat?', '- ...')

    start_date = st.date_input('Tanggal Mulai', value=datetime.date(2025, 4, 1))
    end_date = st.date_input('Tanggal Selesai', min_value=start_date, value=start_date + datetime.timedelta(days=270))

    input_budget = st.text_input('Berapa anggaran untuk proyek ini?', '75,000,000,000.00')
    input_limit_risiko = st.text_input('Berapa Limit Risiko untuk proyek ini?', '5,000,000,000.00')

    return project_description, project_goal, stakeholders, start_date, end_date, input_budget, input_limit_risiko
def process_and_validate_budget(input_budget, input_limit_risiko):
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
            st.error("Format anggaran salah. Masukkan angka valid.")

    if input_limit_risiko:
        try:
            clean_limit_risiko = float(input_limit_risiko.replace(",", ""))
            formatted_limit_risiko = format_number_with_comma(clean_limit_risiko)
            st.session_state.limit_risk = clean_limit_risiko
        except ValueError:
            st.error("Format limit risiko salah. Masukkan angka valid.")

    return clean_budget, clean_limit_risiko, formatted_budget, formatted_limit_risiko


def save_project_data(project_description, project_goal, stakeholders, start_date, end_date, clean_budget, clean_limit_risiko):
    st.session_state.project_description = project_description
    st.session_state.project_goal = project_goal
    st.session_state.stakeholders = stakeholders
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    st.session_state.budget = clean_budget
    st.session_state.limit_risk = clean_limit_risiko
    st.success("Data berhasil disimpan!")
def display_project_recap():
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
    if "gpt_response" in st.session_state:
        risk_list = st.session_state.gpt_response.split('\n')
        relevant_risks = [risk.strip() for risk in risk_list if risk.strip()]

        with st.sidebar:
            selected_risks = []
            st.subheader("Pilih Risiko dari Saran AI")
            for risk in relevant_risks:
                if risk.endswith(':'):
                    st.markdown(f"**{risk}**")
                else:
                    checkbox = st.checkbox(risk, key=f"ai_risk_checkbox_{risk}")
                    if checkbox:
                        selected_risks.append(risk)
            st.session_state.selected_risks = selected_risks
def identify_and_calculate_risks():
    if "selected_risks" in st.session_state:
        st.subheader("3. Identifikasi Risiko")
        inherent_risks = {}
        risk_data = []
        risk_number = 1
        total_inherent_risk_exposure = 0
        limit_risk = st.session_state.limit_risk if "limit_risk" in st.session_state else 1.0

        for risk in st.session_state.selected_risks:
            with st.expander(risk):
                impact = st.text_input(f"Masukkan Nilai Dampak untuk {risk}", '1,000,000,000', key=risk+"_impact")
                if impact:
                    try:
                        clean_impact = float(impact.replace(",", ""))
                        formatted_impact = format_number_with_comma(clean_impact)

                        # Skala dampak
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

                        # Pilihan kemungkinan
                        likelihood_options = {
                            1: "1 - Sangat rendah (< 20%)",
                            2: "2 - Rendah (20% - 40%)",
                            3: "3 - Sedang (40% - 60%)",
                            4: "4 - Tinggi (60% - 80%)",
                            5: "5 - Sangat tinggi (> 80%)"
                        }
                        likelihood_labels = list(likelihood_options.values())
                        likelihood_values = list(likelihood_options.keys())
                        likelihood = st.selectbox(f"Masukkan Skala Kemungkinan untuk {risk}", likelihood_labels, index=2, key=risk+"_likelihood")
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
                    except ValueError:
                        st.error(f"Format dampak salah untuk {risk}. Masukkan angka valid.")

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
            st.table(risk_df)
            st.write(f"Total Inherent Risk Exposure: {format_number_with_comma(total_inherent_risk_exposure)}")
def display_risk_matrix():
    if "Tabel Inherent" in st.session_state:
        st.subheader("5. Matriks Risiko Inherent")
        risk_df = pd.DataFrame(st.session_state["Tabel Inherent"])
        risk_df = risk_df.dropna(subset=["Skala Dampak", "Skala Kemungkinan"])
        risk_df["Skala Dampak"] = risk_df["Skala Dampak"].astype(int)
        risk_df["Skala Kemungkinan"] = risk_df["Skala Kemungkinan"].astype(int)

        risk_labels = {
            (1, 1): ('Low', 1), (1, 2): ('Low', 5), (1, 3): ('Low to Moderate', 10), (1, 4): ('Moderate', 15), (1, 5): ('High', 20),
            (2, 1): ('Low', 2), (2, 2): ('Low to Moderate', 6), (2, 3): ('Low to Moderate', 11), (2, 4): ('Moderate to High', 16), (2, 5): ('High', 21),
            (3, 1): ('Low', 3), (3, 2): ('Low to Moderate', 8), (3, 3): ('Moderate', 13), (3, 4): ('Moderate to High', 18), (3, 5): ('High', 23),
            (4, 1): ('Low', 4), (4, 2): ('Low to Moderate', 9), (4, 3): ('Moderate', 14), (4, 4): ('Moderate to High', 19), (4, 5): ('High', 24),
            (5, 1): ('Low to Moderate', 7), (5, 2): ('Moderate', 12), (5, 3): ('Moderate to High', 17), (5, 4): ('High', 22), (5, 5): ('High', 25)
        }

        color_matrix = np.full((5, 5), 'white', dtype=object)
        risk_matrix_labels = [['' for _ in range(5)] for _ in range(5)]

        for coord, (label, _) in risk_labels.items():
            impact_idx = coord[0] - 1
            likelihood_idx = coord[1] - 1
            if label == 'High':
                color_matrix[likelihood_idx][impact_idx] = 'red'
            elif label == 'Moderate to High':
                color_matrix[likelihood_idx][impact_idx] = 'orange'
            elif label == 'Moderate':
                color_matrix[likelihood_idx][impact_idx] = 'yellow'
            elif label == 'Low to Moderate':
                color_matrix[likelihood_idx][impact_idx] = 'lightgreen'
            elif label == 'Low':
                color_matrix[likelihood_idx][impact_idx] = 'darkgreen'

        for index, row in risk_df.iterrows():
            try:
                skala_dampak = int(row['Skala Dampak'])
                skala_kemungkinan = int(row['Skala Kemungkinan'])
                nomor_risiko = f"#{row['No']}"
                if 1 <= skala_kemungkinan <= 5 and 1 <= skala_dampak <= 5:
                    current_label = risk_matrix_labels[skala_kemungkinan - 1][skala_dampak - 1]
                    risk_matrix_labels[skala_kemungkinan - 1][skala_dampak - 1] = (
                        current_label + ", " + nomor_risiko if current_label else nomor_risiko
                    )
            except ValueError:
                continue

        fig, ax = plt.subplots(figsize=(5, 3), dpi=150)
        for i in range(5):  # likelihood (y-axis)
            for j in range(5):  # impact (x-axis)
                ax.add_patch(plt.Rectangle((j, i), 1, 1, color=color_matrix[i, j], edgecolor='black', linewidth=0.5))
                label, number = risk_labels.get((j + 1, i + 1), ('', ''))
                ax.text(j + 0.5, i + 0.7, label, ha='center', va='center', fontsize=5, color='black')
                ax.text(j + 0.5, i + 0.5, str(number), ha='center', va='center', fontsize=5, color='black')
                ax.text(j + 0.5, i + 0.3, risk_matrix_labels[i][j], ha='center', va='center', fontsize=5, color='blue')

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
        return fig
def edit_and_confirm_mitigations():
    if "selected_risks" in st.session_state:
        st.subheader("6. Edit & Konfirmasi Saran Mitigasi per Risiko")

        if "confirmed_mitigations_per_risk" not in st.session_state:
            st.session_state.confirmed_mitigations_per_risk = {}

        for risk in st.session_state.selected_risks:
            with st.expander(f"Risiko: {risk}"):
                if risk not in st.session_state or st.button(f"Peroleh Saran Mitigasi untuk {risk}", key=f"get_mitigation_{risk}"):
                    st.session_state[risk] = get_risk_handling_suggestions(risk)

                if risk in st.session_state:
                    raw = st.session_state[risk]
                    mitigasi_list = re.findall(r"Program Mitigasi:\s*(.+)", raw)
                    kpi_list = re.findall(r"KPI:\s*([^:]+)", raw)
                    target_kpi_list = re.findall(r"Target KPI:\s*(\d+)", raw)
                    pic_list = re.findall(r"PIC:\s*(.+)", raw)
                    biaya_list = re.findall(r"Biaya:\s*(\d+)", raw)
                    waktu_list = re.findall(r"Waktu Pelaksanaan:\s*(\d+)", raw)

                    max_len = max(len(mitigasi_list), len(kpi_list), len(target_kpi_list), len(pic_list), len(biaya_list), len(waktu_list))
                    mitigasi_list += [""] * (max_len - len(mitigasi_list))
                    kpi_list += [""] * (max_len - len(kpi_list))
                    target_kpi_list += ["0"] * (max_len - len(target_kpi_list))
                    pic_list += ["Belum Ditentukan"] * (max_len - len(pic_list))
                    biaya_list += ["0"] * (max_len - len(biaya_list))
                    waktu_list += ["0"] * (max_len - len(waktu_list))

                    mitigasi_df = pd.DataFrame({
                        "Program Mitigasi": mitigasi_list,
                        "KPI": kpi_list,
                        "Target KPI": list(map(int, target_kpi_list)),
                        "PIC": pic_list,
                        "Biaya": list(map(int, biaya_list)),
                        "Waktu Pelaksanaan": list(map(int, waktu_list)),
                    })

                    edited_df = st.data_editor(mitigasi_df, use_container_width=True, hide_index=True, key=f"edited_{risk}")
                    if st.button(f"Konfirmasi Mitigasi untuk {risk}", key=f"confirm_mitigation_{risk}"):
                        st.session_state.confirmed_mitigations_per_risk[risk] = edited_df
                        st.success(f"✅ Mitigasi untuk '{risk}' berhasil dikonfirmasi!")

        # Gabung semua ke satu tabel
        all_mitigations = []
        for r in st.session_state.selected_risks:
            if r in st.session_state.confirmed_mitigations_per_risk:
                all_mitigations.append(st.session_state.confirmed_mitigations_per_risk[r])

        if all_mitigations:
            st.session_state.all_mitigations = pd.concat(all_mitigations, ignore_index=True)
            st.subheader("✅ Tabel Semua Mitigasi (Final)")
            st.data_editor(st.session_state.all_mitigations, use_container_width=True, hide_index=True, key="final_mitigations")
        else:
            st.info("Belum ada mitigasi yang dikonfirmasi.")
def update_monitoring_kpi():
    if "all_mitigations" not in st.session_state:
        st.session_state["all_mitigations"] = pd.DataFrame()
    if "update_all_mitigation" not in st.session_state:
        st.session_state["update_all_mitigation"] = pd.DataFrame()
    if "monitoring_kpi" not in st.session_state:
        st.session_state["monitoring_kpi"] = pd.DataFrame()

    if st.button("Update All Mitigation"):
        if not st.session_state["all_mitigations"].empty:
            st.session_state["update_all_mitigation"] = st.session_state["all_mitigations"].copy()
            st.success("✅ Data mitigasi disalin ke tabel monitoring.")
            st.session_state["monitoring_kpi"] = pd.DataFrame({
                "Mitigasi Risiko": st.session_state["all_mitigations"]["Program Mitigasi"].tolist(),
                "KPI Triwulan 1": ["" for _ in range(len(st.session_state["all_mitigations"]))],
                "KPI Triwulan 2": ["" for _ in range(len(st.session_state["all_mitigations"]))],
                "KPI Triwulan 3": ["" for _ in range(len(st.session_state["all_mitigations"]))],
                "KPI Triwulan 4": ["" for _ in range(len(st.session_state["all_mitigations"]))],
            })
        else:
            st.error("⚠️ Tidak ada data mitigasi untuk diperbarui.")

    if not st.session_state["monitoring_kpi"].empty:
        st.subheader("📊 Tabel Monitoring KPI")
        edited_kpi = st.data_editor(st.session_state["monitoring_kpi"], use_container_width=True, hide_index=True, key="monitoring_kpi_table")

        if st.button("Update Monitoring KPI"):
            st.session_state["update_monitoring_kpi"] = edited_kpi.copy()
            st.success("✅ Monitoring KPI berhasil diperbarui.")
    else:
        st.warning("Belum ada data monitoring KPI.")
def main():
    st.set_page_config(page_title="RCSA AI", layout="wide")
    setup_streamlit_styles()

    st.title("📌 Aplikasi Risk and Control Self-Assessment (RCSA) Berbasis AI")

    # Langkah 1: Input Proyek
    with st.expander("1. Deskripsi Proyek", expanded=True):
        inputs = get_project_inputs()
        budget_info = process_and_validate_budget(inputs[5], inputs[6])
        if st.button("💾 Simpan Data Proyek"):
            save_project_data(*inputs[:5], *budget_info[:2])
    
    display_project_recap()

    # Langkah 2: Ambil saran risiko dari AI
    if "project_description" in st.session_state and st.button("🤖 Dapatkan Saran Risiko dari AI"):
        st.session_state["gpt_response"] = get_risk_suggestions(
            st.session_state["project_description"],
            st.session_state["project_goal"],
            st.session_state["stakeholders"],
            st.session_state["start_date"],
            st.session_state["end_date"],
            st.session_state["budget"],
            st.session_state["limit_risk"]
        )
        st.success("✅ Saran risiko berhasil diambil dari AI.")

    # Langkah 3: Edit & konfirmasi risiko
    if "gpt_response" in st.session_state:
        display_risk_suggestions()

    # Langkah 4: Identifikasi dan perhitungan inherent risk
    identify_and_calculate_risks()

    # Langkah 5: Matriks risiko
    fig = display_risk_matrix()

    # Langkah 6: Mitigasi risiko
    edit_and_confirm_mitigations()

    # Langkah 7: Monitoring KPI
    update_monitoring_kpi()

    # Langkah 8: Simpan ke Excel
    if st.button("📁 Simpan Hasil ke Excel"):
        session_data = {
            "project_description": st.session_state.get("project_description", ""),
            "project_goal": st.session_state.get("project_goal", ""),
            "stakeholders": st.session_state.get("stakeholders", ""),
            "start_date": st.session_state.get("start_date", ""),
            "end_date": st.session_state.get("end_date", ""),
            "budget": st.session_state.get("budget", 0),
            "limit_risk": st.session_state.get("limit_risk", 0),
            "Tabel Inherent": st.session_state.get("Tabel Inherent", []),
            "all_mitigations": st.session_state.get("all_mitigations", pd.DataFrame()),
            "update_monitoring_kpi": st.session_state.get("update_monitoring_kpi", pd.DataFrame())
        }

        excel_file = save_to_excel(session_data, fig)
        st.download_button(
            label="📥 Unduh Laporan RCSA",
            data=excel_file,
            file_name="rcsa_ai_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
if __name__ == "__main__":
    main()
