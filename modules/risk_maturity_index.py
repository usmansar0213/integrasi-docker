from modules.utils import get_user_file
import streamlit as st
import pandas as pd
import json
import openai
import os
import re
from pathlib import Path
import time
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode

def main():
    # Load API Key from environment variable
    openai.api_key = st.secrets["openai_api_key"]

    # Define default file directory
    uploaded_files_dir = get_user_file("uploaded_files")
    os.makedirs(uploaded_files_dir, exist_ok=True)


    # Initialize session state for uploaded files
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = {}
    if "persisted_files" not in st.session_state:
        st.session_state.persisted_files = {}

    # Ensure uploaded files persist across menu changes
    st.session_state.uploaded_files = st.session_state.persisted_files.copy()

    # Sidebar navigation
    st.sidebar.title("Risk Maturity Index")
    page = st.sidebar.radio("Go to:", ["Home", "Data Assessment", "Data Table", "AI Evaluation", "Expert Evaluation"], key="page")
    
   
    # File uploader for loading saved data
    # Sidebar uploaders
    st.sidebar.subheader("Load Data Pengguna")
    uploaded_load_file = st.sidebar.file_uploader("Upload data file (Excel)", type=["xlsx"], key="load_file")

    st.sidebar.subheader("Upload File Standar Final")
    uploaded_standard_file = st.sidebar.file_uploader("Upload standar final (Excel)", type=["xlsx"], key="standard_file")

    # Save to session state
    if uploaded_standard_file is not None:
        st.session_state.uploaded_standard_file = uploaded_standard_file

            
    if uploaded_load_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_load_file)
            df_params = pd.read_excel(xls, sheet_name="Sheet1")
            df_docs = pd.read_excel(xls, sheet_name="Sheet2")
            
            # Clean column names to remove unexpected spaces
            df_params.columns = df_params.columns.str.strip()
            
            st.session_state.parameters = df_params.to_dict("records")
            st.session_state.saved_data = df_params.set_index("Parameter")["Penjelasan User"].to_dict()
            st.session_state.document_references = df_docs
            st.sidebar.success("Data loaded successfully!")
        except Exception as e:
            st.sidebar.error(f"Error loading data: {e}")

    if "parameters" not in st.session_state:
        st.session_state.parameters = []
        st.session_state.saved_data = {}
        st.session_state.document_references = pd.DataFrame(columns=["Input/Data yang dibutuhkan", "Nama/Dokumen yang Memuat Data"])

    # 1. Judul Aplikasi 
    col1, col2 = st.columns([3, 10])

    # Gunakan path relatif ke logo
    logo_path = os.path.join("static", "via_icon.jpg")

    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
            st.warning("Logo tidak ditemukan di folder static/")

    with col2:
        st.title("Risk Maturity Index Berbasis AI")

    # Save data to Excel
    if st.sidebar.button("Save Data"):
        try:
            df_save = pd.DataFrame(st.session_state.parameters)
            df_files = pd.DataFrame(list(st.session_state.uploaded_files.items()), columns=["Nama/Dokumen yang Memuat Data", "File Path"])
            save_file_path = get_user_file("saved_data.xlsx")
            with pd.ExcelWriter(save_file_path, engine="openpyxl") as writer:
                df_save.to_excel(writer, sheet_name="Sheet1", index=False)
                st.session_state.document_references.to_excel(writer, sheet_name="Sheet2", index=False)
                df_files.to_excel(writer, sheet_name="UploadedFiles", index=False)
            with open(save_file_path, "rb") as f:
                st.sidebar.download_button("Download Saved Data", f, file_name="saved_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.sidebar.success(f"Data saved successfully! File saved at: {save_file_path}")
        except Exception as e:
            st.sidebar.error(f"Error saving data: {e}")




    # Data Assessment Page
    if page == "Data Assessment":
        st.header("Data Assessment")
        df_params = pd.DataFrame(st.session_state.parameters)
        
        if not df_params.empty:
            if "Dimensi" in df_params.columns:
                for idx, (dimensi, group) in enumerate(df_params.groupby("Dimensi"), start=1):
                    with st.expander(f"{idx}. {dimensi}"):
                        for _, row in group.iterrows():
                            st.subheader(row["Parameter"])
                            st.text_area(f"Input for {row['Parameter']}", key=f"input_{row['Parameter']}", value=st.session_state.saved_data.get(row['Parameter'], ""))
        
        # Upload File Referensi
        # Upload File Referensi dengan 2 kolom hanya pada bagian yang relevan
        st.subheader("Upload File Referensi")
        if "Nama/Dokumen yang Memuat Data" in st.session_state.document_references.columns:
            required_files = list(set(st.session_state.document_references["Nama/Dokumen yang Memuat Data"].dropna().tolist()))  # Remove duplicates
            for file_name in required_files:
                with st.expander(f"Upload {file_name}"):
                    col1, col2 = st.columns([2, 3])
                    with col1:
                        uploaded_ref_file = st.file_uploader(f"Upload {file_name}", type=["pdf", "docx", "xlsx", "jpg"], key=f"ref_{file_name}")
                        if uploaded_ref_file is not None:
                            timestamp = time.strftime("%Y%m%d%H%M%S")
                            new_file_name = f"{timestamp}_{uploaded_ref_file.name}"
                            file_path = os.path.join(uploaded_files_dir, new_file_name)
                            with open(file_path, "wb") as f:
                                f.write(uploaded_ref_file.getbuffer())
                            st.session_state.uploaded_files[file_name] = file_path
                            st.session_state.persisted_files[file_name] = file_path
                    with col2:
                        if file_name in st.session_state.uploaded_files:
                            file_path = st.session_state.uploaded_files[file_name]
                            st.write(f"**Path:** {file_path}")
                            with open(file_path, "rb") as f:
                                st.download_button("Download File", f, file_name=os.path.basename(file_path))


    # Data Table Page
    if st.session_state.get("page") == "Data Table":
        st.header("Recap Data Assessment")
        df_params = pd.DataFrame(st.session_state.parameters)
        if not df_params.empty:
            df_params["Input Status"] = df_params["Parameter"].apply(lambda x: 1 if st.session_state.saved_data.get(x, "") else 0)
            recap_table = df_params[["Parameter", "Input Status"]]
            st.markdown(recap_table.to_markdown(index=False))
        else:
            st.write("No data available.")
        
        st.header("Upload File Referensi")
        if st.session_state.uploaded_files:
                st.subheader("Daftar File Referensi yang Diunggah")
                df_uploaded_files = pd.DataFrame(st.session_state.uploaded_files.items(), columns=["Input/Data yang dibutuhkan", "Path Dokumen"])
                st.markdown(df_uploaded_files.to_markdown(index=False))
            
        else:
            st.write("No document references available.")


            
    # Inisialisasi session state jika belum ada
    if "evaluation_results" not in st.session_state:
        st.session_state.evaluation_results = {}

    if "evaluation_scores" not in st.session_state:
        st.session_state.evaluation_scores = {}

    if "parameters" not in st.session_state:
        st.session_state.parameters = []  # Placeholder untuk data pengguna

    if "scores" not in st.session_state:
        st.session_state.scores = []

    if "expert_analysis" not in st.session_state:
        st.session_state.expert_analysis = {}

    save_path = get_user_file("evaluation_results.json")


    def save_results_to_file():
        data_to_save = {
            "evaluation_results": st.session_state.evaluation_results,
            "evaluation_scores": st.session_state.evaluation_scores,
            "expert_analysis": st.session_state.expert_analysis
        }
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        st.success(f"Hasil evaluasi berhasil disimpan ke {save_path}")
        st.write(f"File tersimpan di: `{os.path.abspath(save_path)}`")

    def load_results_from_file():
        if os.path.exists(save_path):
            with open(save_path, "r", encoding="utf-8") as f:
                data_loaded = json.load(f)
                st.session_state.evaluation_results = data_loaded.get("evaluation_results", {}) or {}
                st.session_state.evaluation_scores = data_loaded.get("evaluation_scores", {}) or {}
                st.session_state.expert_analysis = data_loaded.get("expert_analysis", {}) or {}
                st.success("Data evaluasi berhasil dimuat!")

    def display_evaluation_table():
        evaluation_df = pd.DataFrame(list(st.session_state.evaluation_scores.items()), columns=["Parameter", "Nilai Numerik"])
        if not evaluation_df.empty:
            avg_score = evaluation_df["Nilai Numerik"].mean()
            avg_row = pd.DataFrame([("Rata-rata", avg_score)], columns=["Parameter", "Nilai Numerik"])
            evaluation_df = pd.concat([evaluation_df, avg_row], ignore_index=True)
            
            st.subheader("Tabel Hasil Evaluasi")
            st.dataframe(evaluation_df)



    if page == "AI Evaluation":
        st.header("AI Evaluation")
        
        # Load user data
        user_data = pd.DataFrame(st.session_state.parameters)
        
        # Load standar final file dari uploader user
        standard_data = None
        if "uploaded_standard_file" in st.session_state:
            try:
                standard_data = pd.read_excel(st.session_state.uploaded_standard_file)
                st.success("File standar final berhasil dimuat!")
            except Exception as e:
                st.error(f"Error membaca file standar final: {e}")
        else:
            st.warning("File standar final belum di-upload. Silakan upload dulu di sidebar.")

        # Jalankan evaluasi hanya jika standar_data berhasil dimuat
        if standard_data is not None:
            # Sort user data based on numerical order in Parameter
            user_data["Sort_Order"] = user_data["Parameter"].str.extract(r"(\d+)").astype(float)
            user_grouped = user_data.groupby("Parameter")["Penjelasan User"].apply(lambda x: " ".join(x.dropna().astype(str))).reset_index()
            user_grouped = user_grouped.merge(user_data[["Parameter", "Sort_Order"]].drop_duplicates(), on="Parameter")
            user_grouped = user_grouped.sort_values(by="Sort_Order").drop(columns=["Sort_Order"])

            # Ensure session state for evaluation storage
            if "evaluation_df" not in st.session_state:
                st.session_state.evaluation_df = pd.DataFrame(columns=["Parameter", "Penjelasan User", "Hasil Evaluasi", "Nilai Numerik"])
            
            scores = []
            evaluation_scores = {}
            evaluation_results = []
            
            for _, row in user_grouped.iterrows():
                parameter = row["Parameter"]
                user_input = row["Penjelasan User"]

                # Filter only the relevant standard criteria for this parameter
                filtered_standard = standard_data[standard_data["Parameter"] == parameter].to_dict(orient="records")

                evaluation_prompt = {
                    "user_data": {"Parameter": parameter, "User Input": user_input},
                    "standard_criteria": filtered_standard,
                    "instructions": [
                        "Evaluasi masukan pengguna untuk parameter ini.",
                        "Bandingkan dengan kriteria standar berdasarkan fase.",
                        "Pilih fase yang paling mendekati masukan pengguna.",
                        "Berikan penilaian numerik secara terpisah dengan nilai max 5.",
                        "Berikan rekomendasi untuk meningkatkan masukan pengguna."
                    ]
                }

                if st.button(f"Evaluasi {parameter}", key=f"eval_{parameter.replace(' ', '_').replace('.', '').replace(',', '').replace('/', '_')}"):
                    try:
                        response = openai.ChatCompletion.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "Anda adalah seorang ahli dalam evaluasi data kematangan risiko."},
                                {"role": "user", "content": json.dumps(evaluation_prompt, ensure_ascii=False)}
                            ]
                        )

                        evaluation_result = response["choices"][0]["message"]["content"]
                        st.session_state.evaluation_results[parameter] = evaluation_result
                        
                        score_response = openai.ChatCompletion.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": "Hanya berikan angka penilaian numerik tanpa teks tambahan."},
                                {"role": "user", "content": json.dumps(evaluation_prompt, ensure_ascii=False)}
                            ]
                        )
                        
                        score = float(score_response["choices"][0]["message"]["content"].strip())
                        evaluation_scores[parameter] = score
                        scores.append(score)
                        evaluation_results.append([parameter, user_input, evaluation_result, score])
                        st.success(f"Evaluasi untuk {parameter} selesai.")
                        st.write(f"Nilai numerik: {score}")
                        
                        # Append new results to session state dataframe
                        new_data = pd.DataFrame([[parameter, user_input, evaluation_result, score]], columns=["Parameter", "Penjelasan User", "Hasil Evaluasi", "Nilai Numerik"])
                        st.session_state.evaluation_df = pd.concat([st.session_state.evaluation_df, new_data], ignore_index=True)
                    
                    except openai.error.OpenAIError as e:
                        st.error(f"Terjadi kesalahan saat evaluasi: {e}")

                if parameter in st.session_state.evaluation_results:
                    st.text_area(
                        "Hasil Evaluasi",
                        st.session_state.evaluation_results[parameter],
                        height=200
                    )

            # Create a DataFrame for display excluding user input and GPT response
            # Create a DataFrame for display excluding user input and GPT response
            display_df = st.session_state.evaluation_df.drop_duplicates(subset=["Parameter", "Nilai Numerik"])[["Parameter", "Nilai Numerik"]]
            
            st.subheader("Tabel Hasil Evaluasi")
            st.dataframe(display_df, hide_index=True)  # Hide the default index column
            
            # Calculate and display average score in bold
            if not display_df.empty:
                avg_score = display_df["Nilai Numerik"].mean()
                st.markdown(f"**Rata-rata Nilai Evaluasi: {avg_score:.2f}**")
            
            # Save evaluation results to a local file on button click
            if st.button("Save Evaluation"):
                evaluation_file = get_user_file("Evaluation_Results.xlsx")
                st.session_state.evaluation_df.to_excel(evaluation_file, index=False)
                st.success(f"Hasil evaluasi disimpan di: {evaluation_file}")
            


    if page == "Home":
        st.write("""
        ### Penjelasan
        Aplikasi yang berbasis Artificial Intelligence (AI) ini dirancang untuk membantu perusahaan 
        dalam pelaksanaan Indeks Maturitas Risiko atau Risk Maturity Index (RMI) 
        berdasarkan Permen BUMN Nomor PER-02/MBU/03/2023 tahun 2023 tentang Tata
        Kelola dan Kegiatan Korporasi Signifikan BUMN. Aplikasi ini mencakup berbagai aspek
        penting yang harus dipatuhi BUMN untuk memastikan tata kelola yang baik dan manajemen
        risiko yang efektif, termasuk kewajiban untuk melakukan penilaian terhadap maturitas
        manajemen risiko yang diterapkan. Ini merupakan alat penting untuk memastikan
        bahwa BUMN memiliki sistem dan proses manajemen risiko yang matang, yang dapat
        mendukung tata kelola yang baik dan keberlanjutan perusahaan dalam jangka panjang.
        
        ### Keuntungan Menggunakan Aplikasi Ini
        - Membantu organisasi memahami posisi mereka dalam kematangan manajemen risiko
        - Memberikan umpan balik berdasarkan standar kematangan risiko
        - Menyediakan laporan dan rekomendasi untuk perbaikan
        - Menyediakan evaluasi umum dengan memanfaatkan AI
        - Menyediakan validasi menyeluruh dari Ahli Manajemen Risiko
        - Dapat digunakan oleh berbagai level manajemen untuk evaluasi
        
        ### Menu dan Langkah Penggunaan
        1. **Assessment**: Mengisi jawaban terkait parameter manajemen risiko.
        2. **Data Table**: Melihat ringkasan jawaban yang telah diisi.
        3. **AI Evaluation**: Mendapatkan hasil evaluasi berdasarkan jawaban yang telah diberikan.
        4. **Expert Evaluation**: Memungkinkan evaluasi tambahan oleh pakar untuk validasi hasil.
        
        Mulailah dengan masuk ke halaman "Assessment" dan isi setiap parameter yang tersedia.
        """)

    # Define page
    if page == "Expert Evaluation":
        st.header("Expert Evaluation")
        
        
        
        # Display evaluation dataframe using AgGrid
        st.subheader("Tabel Hasil Evaluasi")
        if "evaluation_df" in st.session_state and not st.session_state.evaluation_df.empty:
            evaluation_df = st.session_state.evaluation_df[["Parameter", "Nilai Numerik"]]
            
            gb = GridOptionsBuilder.from_dataframe(evaluation_df)
            gb.configure_columns(["Nilai Numerik"], editable=True)
            grid_options = gb.build()
            
            grid_response = AgGrid(
                evaluation_df,
                gridOptions=grid_options,
                columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                height=300,
                theme="material",
                editable=True
            )
            
            # Update session state with edited data
            updated_df = grid_response["data"]
            st.session_state.evaluation_df.update(updated_df)
            
            # Calculate and display average score
            if not updated_df.empty:
                avg_score = updated_df["Nilai Numerik"].mean()
                st.markdown(f"**Rata-rata Nilai Evaluasi: {avg_score:.2f}**")
        else:
            st.warning("Belum ada data evaluasi yang tersedia.")
        # Display evaluation results
        st.subheader("Hasil Evaluasi")
        if "evaluation_results" in st.session_state and st.session_state.evaluation_results:
            for parameter, evaluation in st.session_state.evaluation_results.items():
                st.markdown(f"### {parameter}")
                st.text_area("Evaluasi GPT:", evaluation, height=200)
        else:
            st.warning("Belum ada hasil evaluasi yang tersedia. Silakan lakukan AI Evaluation terlebih dahulu.")    
