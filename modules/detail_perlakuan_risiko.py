import streamlit as st
import pandas as pd
import openai
import os
import io
import re
import json
from datetime import datetime

openai.api_key = os.getenv("OPENAI_API_KEY")

def bersihkan_output_gpt(text):
    text = text.replace("“", "\"").replace("”", "\"")
    text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE)
    return text.strip()

def get_gpt_quarter_programs_per_risiko(df_gabungan: pd.DataFrame) -> pd.DataFrame:
    hasil = []
    total = len(df_gabungan)
    progress_bar = st.progress(0, text="🚀 Mengirim ke GPT...")

    for i, (_, row) in enumerate(df_gabungan.iterrows()):
        kode_risiko = row.get("Kode Risiko", "")
        rencana = row.get("Rencana Perlakuan Risiko", "")
        pic = row.get("PIC", "")
        jenis_rkap = row.get("Jenis Program Dalam RKAP", "")

        prompt = f"""
Buatkan rencana program per quarter untuk mitigasi risiko berikut ini.

Informasi mitigasi:
- Kode Risiko: {kode_risiko}
- Rencana Perlakuan Risiko: {rencana}
- PIC: {pic}
- Jenis Program Dalam RKAP: {jenis_rkap}

Format jawaban HARUS dalam JSON seperti ini:
{{
  "Rencana Quarter": {{
    "Kode Risiko": "...",
    "Rencana Perlakuan Risiko": "...",
    "PIC": "...",
    "Jenis Program Dalam RKAP": "...",
    "Program Q1": "...",
    "Program Q2": "...",
    "Program Q3": "...",
    "Program Q4": "..."
  }}
}}

TANPA tambahan penjelasan atau markdown!
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            content = response.choices[0].message.content.strip()
            content = bersihkan_output_gpt(content)
            json_raw = re.search(r"\{.*\}", content, re.DOTALL).group(0)
            data = json.loads(json_raw)
            hasil.append(data.get("Rencana Quarter", {}))  # satu dict per risiko

        except Exception as e:
            st.warning(f"⚠️ Gagal untuk Kode Risiko {kode_risiko}: {e}")

        # Update progress bar
        progress = int((i + 1) / total * 100)
        progress_bar.progress((i + 1) / total, text=f"📦 Memproses {i + 1} dari {total} risiko...")

    progress_bar.empty()  # hilangkan progress bar setelah selesai
    return pd.DataFrame(hasil)

def update_quarter_mitigasi(df_terbaru):
    st.session_state["copy_quarter_mitigasi"] = df_terbaru.copy()
    st.success("✅ Data telah diperbarui di session state.")

def save_quarter_mitigasi_dengan_download():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_path = "C:/saved"
    judul = "detail_perlakuan_risiko"  # nama file tanpa ekstensi

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filename = f"{judul}_{timestamp}.xlsx"
    server_file_path = os.path.join(folder_path, filename)
    output = io.BytesIO()

    df_quarter = st.session_state.get("copy_quarter_mitigasi", pd.DataFrame())
    if df_quarter.empty:
        st.warning("⚠️ Tidak ada data rencana quarter yang tersedia untuk disimpan.")
        return

    with pd.ExcelWriter(server_file_path, engine="xlsxwriter") as writer_server, \
         pd.ExcelWriter(output, engine="xlsxwriter") as writer_download:

        df_save = df_quarter.copy()
        if "Nomor" in df_save.columns:
            df_save = df_save.drop(columns=["Nomor"])
        df_save.insert(0, "Nomor", range(1, len(df_save) + 1))

        df_save.to_excel(writer_server, sheet_name="Detail Perlakuan Risiko", index=False)
        df_save.to_excel(writer_download, sheet_name="Detail Perlakuan Risiko", index=False)

    output.seek(0)

    st.download_button(
        label="⬇️ Unduh Detail Perlakuan Risiko",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def main():
    st.title("📆 Detail Perlakuan Risiko")

    # LETACS: Loader
    uploaded_file = st.file_uploader("Silahkan Unggah file: Perlakuan Risiko ["xlsx"])
    if uploaded_file:
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = [s.lower() for s in xls.sheet_names]

            # Load sheet Deskripsi Mitigasi
            if "deskripsi mitigasi" in sheet_names:
                df_mitigasi = xls.parse("Deskripsi Mitigasi")
                if {"Kode Risiko", "Rencana Perlakuan Risiko"}.issubset(df_mitigasi.columns):
                    st.session_state["copy_tabel_deskripsi_mitigasi"] = df_mitigasi
                    st.success("✅ Sheet 'Deskripsi Mitigasi' berhasil dimuat.")
                else:
                    st.warning("⚠️ Sheet 'Deskripsi Mitigasi' tidak memiliki kolom wajib.")

            # Load sheet Anggaran PIC
            if "anggaran pic" in sheet_names:
                df_anggaran = xls.parse("Anggaran PIC")
                if {"Kode Risiko", "PIC", "Jenis Program Dalam RKAP"}.issubset(df_anggaran.columns):
                    st.session_state["copy_tabel_anggaran_pic"] = df_anggaran
                    st.success("✅ Sheet 'Anggaran PIC' berhasil dimuat.")
                else:
                    st.warning("⚠️ Sheet 'Anggaran PIC' tidak memiliki kolom wajib.")

            # Load sheet Detail Perlakuan Risiko (hasil ekspor)
            if "detail perlakuan risiko" in sheet_names:
                df_quarter = xls.parse("Detail Perlakuan Risiko")
                if {"Kode Risiko", "Program Q1", "Program Q2", "Program Q3", "Program Q4"}.issubset(df_quarter.columns):
                    st.session_state["copy_quarter_mitigasi"] = df_quarter
                    st.success("✅ Sheet 'Detail Perlakuan Risiko' berhasil dimuat.")
                else:
                    st.warning("⚠️ Sheet 'Detail Perlakuan Risiko' tidak memiliki kolom wajib.")

        except Exception as e:
            st.error(f"❌ Gagal membaca file: {e}")

    # LETACS: Establish + Auth
    with st.expander("📌 Tabel Deskripsi Mitigasi, Anggaran & PIC"):
        df_mitigasi = st.session_state.get("copy_tabel_deskripsi_mitigasi", pd.DataFrame())
        df_anggaran = st.session_state.get("copy_tabel_anggaran_pic", pd.DataFrame())

        if not df_mitigasi.empty:
            st.markdown("### 📋 Deskripsi Mitigasi")
            st.dataframe(df_mitigasi, use_container_width=True)
        else:
            st.info("ℹ️ Tabel Deskripsi Mitigasi belum tersedia.")

        if not df_anggaran.empty:
            st.markdown("### 💰 Anggaran & PIC")
            st.dataframe(df_anggaran, use_container_width=True)
        else:
            st.info("ℹ️ Tabel Anggaran & PIC belum tersedia.")

        if not df_mitigasi.empty and not df_anggaran.empty:
            df_gabungan = pd.merge(df_mitigasi, df_anggaran, on="Kode Risiko", how="left")
            st.markdown("### 🔗 Gabungan Mitigasi + Anggaran & PIC")
            st.dataframe(df_gabungan, use_container_width=True)
        else:
            st.info("ℹ️ Tidak bisa menggabungkan tabel karena salah satu masih kosong.")

    if st.button("📆 Dapatkan Rencana Program per Quarter dari GPT"):
        if not df_mitigasi.empty and not df_anggaran.empty:
            df_gabungan = pd.merge(df_mitigasi, df_anggaran, on="Kode Risiko", how="left")
            with st.spinner("⏳ Mengirim data satu per satu ke GPT..."):
                progress_bar = st.progress(0)
                df_quarter = get_gpt_quarter_programs_per_risiko(df_gabungan)
                progress_bar.progress(1.0)
            if not df_quarter.empty:
                update_quarter_mitigasi(df_quarter)
        else:
            st.warning("⚠️ Data deskripsi mitigasi dan anggaran belum lengkap.")

    if "copy_quarter_mitigasi" in st.session_state:
        st.subheader("🛠️ Rencana Program per Quarter (silakan lengkapi % progress)")
        df_quarter_edit = st.data_editor(
            st.session_state["copy_quarter_mitigasi"],
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key="editor_quarter"
        )

        if st.button("🔄 Update Data"):
            update_quarter_mitigasi(df_quarter_edit)

        save_quarter_mitigasi_dengan_download()
