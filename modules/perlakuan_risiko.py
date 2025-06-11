import streamlit as st
import pandas as pd
import json
import openai
import os
import re
import time
import json5
from datetime import datetime
from datetime import datetime
import io

# Konstanta Label
BTN_SAVE_LABEL = "💾 Simpan Data ke Excel"
BTN_GET_AI_LABEL = "🤖 Dapatkan Saran AI"
BTN_LOAD_LABEL = "📂 Muat Data dari File"

# Inisialisasi API Key OpenAI
openai.api_key = st.secrets["openai_api_key"]

def upload_semua_file_risiko():
    with st.expander("📥 Upload Semua File Risiko (Strategi, Inherent, Mitigasi)", expanded=True):
        uploaded_files = st.file_uploader(
            "Unggah Maksimal 3 File Excel (Strategi Risiko, Inherent Risk, Hasil Mitigasi)", 
            type=["xlsx"], 
            accept_multiple_files=True, 
            key="upload_semua"
        )

        file_strategi = None
        file_inherent = None
        file_mitigasi = None

        for f in uploaded_files:
            try:
                xls = pd.ExcelFile(f)
                sheet_names = [s.lower() for s in xls.sheet_names]

                if any("kuantitatif" in s or "kualitatif" in s for s in sheet_names):
                    file_inherent = f
                elif any("deskripsi mitigasi" in s or "anggaran pic" in s for s in sheet_names):
                    file_mitigasi = f
                elif any("strategi" in f.name.lower() or "aset" in s for s in sheet_names):
                    file_strategi = f

            except Exception as e:
                st.error(f"❌ Tidak bisa membaca file: {f.name}. Error: {e}")

        # === Proses file strategi ===
        if file_strategi:
            try:
                xls = pd.ExcelFile(file_strategi)
                for sheet in xls.sheet_names:
                    df_sheet = pd.read_excel(xls, sheet_name=sheet)
                    baris_limit = df_sheet[df_sheet.iloc[:, 0].astype(str).str.lower().str.contains("limit risiko", na=False)]
                    if not baris_limit.empty:
                        nilai_limit = pd.to_numeric(baris_limit.iloc[0, 1], errors='coerce')
                        if pd.notna(nilai_limit) and nilai_limit > 0:
                            st.session_state["copy_limit_risiko"] = nilai_limit
                            formatted = f"Rp {nilai_limit:,.0f}".replace(",", ".")
                            st.success(f"✅ Limit Risiko ditemukan: {formatted}")
                            break
                else:
                    st.warning("⚠️ Baris 'Limit Risiko' tidak ditemukan.")
            except Exception as e:
                st.error(f"❌ Gagal membaca file strategi: {e}")

        # === Proses file inherent ===
        if file_inherent:
            try:
                xls = pd.ExcelFile(file_inherent)
                df_kuantitatif = pd.read_excel(xls, sheet_name="Tabel Kuantitatif")
                df_kualitatif = pd.read_excel(xls, sheet_name="Tabel Kualitatif")
                st.session_state["copy_Risiko_Kuantitatif"] = df_kuantitatif
                st.session_state["copy_Risiko_Kualitatif"] = df_kualitatif
                st.success("✅ Data Risiko Kuantitatif & Kualitatif berhasil dimuat.")
            except Exception as e:
                st.error(f"❌ Gagal membaca file inherent risk: {e}")

        # === Proses file mitigasi ===
        if file_mitigasi:
            try:
                xls = pd.ExcelFile(file_mitigasi)

                if "Deskripsi Mitigasi" in xls.sheet_names:
                    df_mitigasi = pd.read_excel(xls, sheet_name="Deskripsi Mitigasi")
                    st.session_state["copy_tabel_deskripsi_mitigasi"] = df_mitigasi
                    st.success("✅ Deskripsi Mitigasi berhasil dimuat.")
                else:
                    df_mitigasi = pd.DataFrame()

                if "Anggaran PIC" in xls.sheet_names:
                    df_anggaran = pd.read_excel(xls, sheet_name="Anggaran PIC")
                    st.session_state["copy_tabel_anggaran_pic"] = df_anggaran
                    st.success("✅ Anggaran PIC berhasil dimuat.")
                else:
                    df_anggaran = pd.DataFrame()

                if "Total Biaya" in xls.sheet_names:
                    total_biaya_df = pd.read_excel(xls, sheet_name="Total Biaya")
                    if not total_biaya_df.empty and "Total Biaya Perlakuan Risiko" in total_biaya_df.columns:
                        st.session_state["copy_total_biaya_mitigasi"] = int(total_biaya_df["Total Biaya Perlakuan Risiko"].iloc[0])
                        st.session_state["copy_tabel_total_biaya"] = total_biaya_df
                        st.success("✅ Total Biaya berhasil dimuat.")

                if not df_mitigasi.empty or not df_anggaran.empty:
                    st.session_state["detail_mitigasi"] = {
                        "Mitigasi": df_mitigasi.to_dict("records"),
                        "AnggaranPIC": df_anggaran.to_dict("records")
                    }
                    st.info("🔁 Data detail_mitigasi diperbarui dari file.")

            except Exception as e:
                st.error(f"❌ Gagal membaca file mitigasi: {e}")


def gabungkan_tabel_risiko():
    if 'copy_Risiko_Kuantitatif' in st.session_state and 'copy_Risiko_Kualitatif' in st.session_state:
        df_kuantitatif = st.session_state['copy_Risiko_Kuantitatif'].copy()
        df_kualitatif = st.session_state['copy_Risiko_Kualitatif'].copy()

        df_kuantitatif['Tipe Risiko'] = 'Kuantitatif'
        df_kualitatif['Tipe Risiko'] = 'Kualitatif'

        df_gabungan = pd.concat([df_kuantitatif, df_kualitatif], ignore_index=True)

        return df_gabungan
    else:
        return None
def get_gpt_risk_mitigation(df_risiko):
    if "Kode Risiko" not in df_risiko.columns:
        st.error("❌ Kolom 'Kode Risiko' tidak ditemukan dalam data.")
        return {}

    df_risiko['Unique Identifier'] = df_risiko.apply(lambda row: f"{row['Kode Risiko']}_{row['Peristiwa Risiko']}", axis=1)
    daftar_risiko = df_risiko[["Unique Identifier", "Kode Risiko", "Peristiwa Risiko"]].dropna()

    all_mitigasi = []
    total_risks = len(daftar_risiko)
    progress = st.progress(0)

    for i, (_, row) in enumerate(daftar_risiko.iterrows()):
        prompt = f"""
        Berikan 3 rekomendasi mitigasi risiko untuk peristiwa risiko berikut:

        - [{row['Unique Identifier']}] {row['Peristiwa Risiko']}

        Format output harus dalam JSON **tanpa tambahan teks lain**:
        ```json
        {{
            "mitigasi": [
                {{
                    "Kode Risiko": "{row['Kode Risiko']}",
                    "Peristiwa": "{row['Peristiwa Risiko']}",
                    "Rekomendasi": ["Mitigasi 1", "Mitigasi 2", "Mitigasi 3"]
                }}
            ]
        }}
        ```
        """

        with st.spinner(f"⏳ Memproses peristiwa risiko: {row['Peristiwa Risiko']}..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )

                raw_output = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                json_part = raw_output[raw_output.find("{"): raw_output.rfind("}") + 1]
                mitigasi_dict = json.loads(json_part)

                if "mitigasi" in mitigasi_dict:
                    all_mitigasi.append(mitigasi_dict["mitigasi"][0])
                else:
                    st.warning(f"⚠️ Tidak ada rekomendasi mitigasi untuk peristiwa risiko: {row['Peristiwa Risiko']}.")

            except json.JSONDecodeError:
                st.error(f"❌ Format data yang diterima dari GPT tidak valid untuk peristiwa: {row['Peristiwa Risiko']}")
                continue
            except Exception as e:
                st.error(f"❌ Error saat memproses peristiwa risiko: {row['Peristiwa Risiko']}. Error: {e}")
                continue

        progress.progress((i + 1) / total_risks)

    st.session_state["mitigasi_risiko"] = {"mitigasi": all_mitigasi}
    return {"mitigasi": all_mitigasi}



def get_gpt_mitigation_deskripsi(kode_risiko: str, peristiwa: str, mitigasi: str) -> list:
    prompt = f"""
Berikan Tabel Deskripsi Mitigasi untuk risiko berikut dalam format JSON PENUH:

Kode Risiko: {kode_risiko}
Peristiwa Risiko: {peristiwa}
Mitigasi yang direncanakan: {mitigasi}

Struktur kolom yang DIBUTUHKAN:
- Kode Risiko
- Peristiwa Risiko
- Penyebab Risiko
- Opsi Perlakuan Risiko
- Jenis Rencana Perlakuan Risiko
- Rencana Perlakuan Risiko
- Output Perlakuan Risiko

Format:
{{
  "Tabel Deskripsi Mitigasi": [
    {{
      "Kode Risiko": "...",
      "Peristiwa Risiko": "...",
      "Penyebab Risiko": "...",
      "Opsi Perlakuan Risiko": "...",
      "Jenis Rencana Perlakuan Risiko": "...",
      "Rencana Perlakuan Risiko": "...",
      "Output Perlakuan Risiko": "..."
    }}
  ]
}}

⚠️ Jangan menambahkan penjelasan, komentar, atau markdown. JSON SAJA.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        content = bersihkan_output_gpt(content)
        data = json.loads(re.search(r"\{.*\}", content, re.DOTALL).group(0))
        deskripsi = data.get("Tabel Deskripsi Mitigasi", [])
        return [deskripsi] if isinstance(deskripsi, dict) else deskripsi
    except Exception as e:
        st.error(f"❌ Error saat deskripsi mitigasi '{peristiwa}': {e}")
        return []

def get_gpt_mitigation_anggaran(kode_risiko: str, peristiwa: str, mitigasi: str, eksposur: float, persen_biaya: float = 0.02) -> list:
    biaya = int(eksposur * persen_biaya)
    prompt = f"""
Berikan Tabel Anggaran & PIC untuk risiko berikut dalam format JSON PENUH:

Kode Risiko: {kode_risiko}
Peristiwa Risiko: {peristiwa}
Mitigasi yang direncanakan: {mitigasi}
Eksposur Risiko: {eksposur}
Biaya Perlakuan Risiko (2% dari eksposur): {biaya}

Struktur kolom yang DIBUTUHKAN:
- Kode Risiko
- Peristiwa Risiko
- Biaya Perlakuan Risiko
- Jenis Program Dalam RKAP
- PIC
- Timeline (Bulan Mulai)
- Timeline (Bulan Selesai)

Format:
{{
  "Tabel Anggaran & PIC": [
    {{
      "Kode Risiko": "...",
      "Peristiwa Risiko": "...",
      "Biaya Perlakuan Risiko": ...,
      "Jenis Program Dalam RKAP": "...",
      "PIC": "...",
      "Timeline (Bulan Mulai)": "...",
      "Timeline (Bulan Selesai)": "..."
    }}
  ]
}}

⚠️ Jangan menambahkan penjelasan, komentar, atau markdown. JSON SAJA.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        content = bersihkan_output_gpt(content)
        data = json.loads(re.search(r"\{.*\}", content, re.DOTALL).group(0))
        anggaran = data.get("Tabel Anggaran & PIC", [])
        return [anggaran] if isinstance(anggaran, dict) else anggaran
    except Exception as e:
        st.error(f"❌ Error saat anggaran mitigasi '{peristiwa}': {e}")
        return []

def update_selected_mitigation():
    if "selected_mitigasi" in st.session_state and st.session_state["selected_mitigasi"]:
        st.session_state["copy_selected_mitigasi"] = st.session_state["selected_mitigasi"].copy()
        st.success("✅ Mitigasi telah diperbarui dan disalin ke 'copy_selected_mitigasi'.")
    else:
        st.error("❌ Tidak ada mitigasi yang dipilih untuk diperbarui.")

def update_copy_tables():
    """
    Menyimpan versi final hasil edit dari session_state (temp/draft) ke copy_*
    agar siap disimpan ke file Excel, termasuk menghitung total biaya mitigasi.
    """
    # Update mitigasi
    if "detail_mitigasi" in st.session_state:
        detail = st.session_state["detail_mitigasi"]
        if "Mitigasi" in detail:
            df_mitigasi = pd.DataFrame(detail["Mitigasi"])
            if not df_mitigasi.empty:
                st.session_state["copy_tabel_deskripsi_mitigasi"] = df_mitigasi
        if "AnggaranPIC" in detail:
            df_anggaran = pd.DataFrame(detail["AnggaranPIC"])
            if not df_anggaran.empty:
                st.session_state["copy_tabel_anggaran_pic"] = df_anggaran

    # Update hasil editor jika ada (misalnya editor_anggaran)
    edited_anggaran = st.session_state.get("editor_anggaran", None)
    if isinstance(edited_anggaran, pd.DataFrame) and not edited_anggaran.empty:
        st.session_state["copy_tabel_anggaran_pic"] = edited_anggaran

    # Hitung dan simpan Total Biaya Perlakuan Risiko
    df_final_anggaran = st.session_state.get("copy_tabel_anggaran_pic", pd.DataFrame())
    if not df_final_anggaran.empty and "Biaya Perlakuan Risiko" in df_final_anggaran.columns:
        biaya_col = df_final_anggaran["Biaya Perlakuan Risiko"].astype(str).str.replace(r"[^\d]", "", regex=True)
        df_final_anggaran["Biaya Perlakuan Risiko"] = pd.to_numeric(biaya_col, errors="coerce").fillna(0)
        total_biaya = int(df_final_anggaran["Biaya Perlakuan Risiko"].sum())

        st.session_state["copy_total_biaya_mitigasi"] = total_biaya
        st.session_state["copy_tabel_total_biaya"] = pd.DataFrame([{"Total Biaya Perlakuan Risiko": total_biaya}])

    else:
        st.warning("⚠️ Tidak dapat menghitung total biaya karena kolom tidak ditemukan atau data kosong.")

def bersihkan_output_gpt(text):
    text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"[‘’]", "'", text)
    text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE)
    return text.strip()


def hitung_total_biaya_perlakuan(df_anggaran):
    if df_anggaran is not None and not df_anggaran.empty:
        if "Biaya Perlakuan Risiko" in df_anggaran.columns:
            biaya_clean = df_anggaran["Biaya Perlakuan Risiko"].astype(str).str.replace(r"[^\d]", "", regex=True)
            df_anggaran["Biaya Perlakuan Risiko"] = pd.to_numeric(biaya_clean, errors="coerce").fillna(0)
            total_biaya = int(df_anggaran["Biaya Perlakuan Risiko"].sum())

            formatted_total = f"{total_biaya:,}".replace(",", ".")

            # Simpan ke session state
            st.session_state["copy_total_biaya_mitigasi"] = total_biaya
            st.session_state["copy_tabel_total_biaya"] = pd.DataFrame([
                {"Total Biaya Perlakuan Risiko": total_biaya}
            ])

            return total_biaya, formatted_total
    return 0, "0"

def save_updated_data_to_excel():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_path = "C:/saved"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    server_file_path = os.path.join(folder_path, f"perlakuan_risiko_{timestamp}.xlsx")
    output = io.BytesIO()

    df_mitigasi = st.session_state.get("copy_tabel_deskripsi_mitigasi", pd.DataFrame())
    df_anggaran = st.session_state.get("copy_tabel_anggaran_pic", pd.DataFrame())
    df_total = st.session_state.get("copy_tabel_total_biaya", pd.DataFrame())

    if df_mitigasi.empty or df_anggaran.empty:
        st.warning("⚠️ Tabel Deskripsi Mitigasi atau Anggaran PIC belum tersedia. Tidak bisa menyimpan file.")
        return

    with pd.ExcelWriter(server_file_path, engine='xlsxwriter') as writer_server, \
         pd.ExcelWriter(output, engine='xlsxwriter') as writer_download:

        for sheet_name, df in {
            "Deskripsi Mitigasi": df_mitigasi,
            "Anggaran PIC": df_anggaran,
            "Total Biaya": df_total
        }.items():
            df_save = df.copy()
            if not df_save.empty:
                if "Nomor" in df_save.columns:
                    df_save = df_save.drop(columns=["Nomor"])
                df_save.insert(0, "Nomor", range(1, len(df_save) + 1))
                df_save.to_excel(writer_server, sheet_name=sheet_name, index=False)
                df_save.to_excel(writer_download, sheet_name=sheet_name, index=False)

    output.seek(0)

    st.download_button(
        label="⬇️ Unduh File Perlakuan Risiko",
        data=output,
        file_name=f"perlakuan_risiko_{timestamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def main():
    st.title("📊 Perlakuan Risiko")
    upload_semua_file_risiko()
    df_gabungan = gabungkan_tabel_risiko()
    if df_gabungan is not None:
        st.session_state["df_risiko_gabungan_terbaru"] = df_gabungan

    # ✅ Tampilkan data awal dan validasi kelengkapan
    with st.expander("📂 Lihat Data Risiko Awal (Kuantitatif, Kualitatif, dan Gabungan)"):
        risiko_q = st.session_state.get('copy_Risiko_Kuantitatif')
        risiko_k = st.session_state.get('copy_Risiko_Kualitatif')
        limit_risiko = st.session_state.get('copy_limit_risiko')

        # Risiko Kuantitatif
        if risiko_q is not None:
            st.markdown("### 📊 Risiko Kuantitatif")
            st.dataframe(risiko_q, use_container_width=True)
        else:
            st.info("ℹ️ Data Risiko Kuantitatif belum tersedia.")

        # Risiko Kualitatif
        if risiko_k is not None:
            st.markdown("### 📊 Risiko Kualitatif")
            st.dataframe(risiko_k, use_container_width=True)
        else:
            st.info("ℹ️ Data Risiko Kualitatif belum tersedia.")

        # Gabungan Risiko
        if df_gabungan is not None:
            st.markdown("### 📊 Gabungan Risiko")
            st.dataframe(df_gabungan, use_container_width=True)
        else:
            st.info("ℹ️ Data Gabungan Risiko belum tersedia.")

        # Limit Risiko
        if limit_risiko is not None:
            st.subheader("📌 Limit Risiko")
            if isinstance(limit_risiko, pd.DataFrame):
                st.dataframe(limit_risiko, use_container_width=True)
            elif isinstance(limit_risiko, (int, float)):
                formatted_value = f"Rp {limit_risiko:,.0f}".replace(",", ".")
                st.success(f"💰 **Total Limit Risiko:** {formatted_value}")
            else:
                st.write("📄 Limit Risiko:", limit_risiko)
        else:
            st.info("ℹ️ Data Limit Risiko belum tersedia.")

    # ✅ Validasi kelengkapan data
    if risiko_q is not None and risiko_k is not None and df_gabungan is not None:
        st.success("✅ Data sudah lengkap. Silakan lanjutkan proses.")
    else:
        st.warning("⚠️ Data belum lengkap. Harap lengkapi Risiko Kuantitatif dan Kualitatif terlebih dahulu.")


    if st.button("🚀 Mulai Proses GPT"):
        if "df_risiko_gabungan_terbaru" in st.session_state:
            df_risiko = st.session_state["df_risiko_gabungan_terbaru"]
            if "Peristiwa Risiko" in df_risiko.columns:
                st.session_state["mitigasi_risiko"] = get_gpt_risk_mitigation(df_risiko)
            else:
                st.error("❌ Kolom 'Peristiwa Risiko' tidak ditemukan pada data.")
        else:
            st.error("❌ Data risiko gabungan belum tersedia.")

    if "mitigasi_risiko" in st.session_state:
        st.subheader("📋 Rekomendasi Mitigasi Risiko")

        if "selected_mitigasi" not in st.session_state:
            st.session_state["selected_mitigasi"] = []
        selected_mitigasi = st.session_state["selected_mitigasi"]

        for idx, peristiwa_obj in enumerate(st.session_state["mitigasi_risiko"].get("mitigasi", [])):
            kode = peristiwa_obj.get("Kode Risiko", f"❓{idx}")
            peristiwa = peristiwa_obj.get("Peristiwa", f"[Tanpa Nama {idx}]")

            st.markdown(f"**[{kode}] {peristiwa}**")

            rekomendasi_list = peristiwa_obj.get("Rekomendasi", [])
            if not isinstance(rekomendasi_list, list):
                st.warning(f"⚠️ Rekomendasi untuk '{peristiwa}' tidak dalam bentuk list. Melewati.")
                continue

            for i, mitigasi in enumerate(rekomendasi_list):
                if isinstance(mitigasi, str):
                    checkbox_key = f"{kode}_{i}_{peristiwa[:20]}"
                    if st.checkbox(mitigasi, key=checkbox_key):
                        item = {
                            "Kode Risiko": kode,
                            "Peristiwa": peristiwa,
                            "Mitigasi": mitigasi
                        }
                        if item not in selected_mitigasi:
                            selected_mitigasi.append(item)
                else:
                    st.error(f"❌ Data mitigasi ke-{i} untuk '{peristiwa}' bukan string.")

    if "selected_mitigasi" in st.session_state:
        st.subheader("✅ Selected Mitigation (silahkan edit)")
        df_selected = pd.DataFrame(st.session_state["selected_mitigasi"])
        if not df_selected.empty:
            df_selected.insert(0, "No", range(1, len(df_selected) + 1))
        st.data_editor(df_selected, hide_index=True, use_container_width=True, num_rows="dynamic")


        
        if st.button("🔄 Update Mitigasi"):
            update_selected_mitigation()
            
        if st.button("🚀 Dapatkan Rekomendasi Detail Mitigasi"):
            selected_mitigasi = st.session_state.get("copy_selected_mitigasi", [])

            if not selected_mitigasi:
                st.error("❌ Tidak ada mitigasi yang dipilih.")
            elif "df_risiko_gabungan_terbaru" not in st.session_state:
                st.error("❌ Data risiko gabungan belum tersedia.")
            else:
                df_risiko = st.session_state["df_risiko_gabungan_terbaru"]
                df_risiko["Peristiwa Risiko Clean"] = df_risiko["Peristiwa Risiko"].astype(str).str.strip().str.lower()

                all_deskripsi = []
                all_anggaran = []
                gagal_proses = []

                progress = st.progress(0, text="⏳ Memproses mitigasi...")

                for i, m in enumerate(selected_mitigasi):
                    kode = m.get("Kode Risiko", "❓")
                    peristiwa = m.get("Peristiwa", "").strip()
                    aksi = m.get("Mitigasi", "").strip()
                    peristiwa_clean = peristiwa.lower()

                    eksposur = 0
                    match = df_risiko[df_risiko["Peristiwa Risiko Clean"] == peristiwa_clean]
                    if not match.empty and "Eksposur Risiko" in match.columns:
                        eksposur = match["Eksposur Risiko"].astype(float).max()

                    try:
                        deskripsi = get_gpt_mitigation_deskripsi(kode, peristiwa, aksi)
                        anggaran = get_gpt_mitigation_anggaran(kode, peristiwa, aksi, eksposur, 0.02)

                        if deskripsi:
                            all_deskripsi.extend(deskripsi)
                        else:
                            gagal_proses.append(f"[{kode}] Deskripsi")

                        if anggaran:
                            all_anggaran.extend(anggaran)
                        else:
                            gagal_proses.append(f"[{kode}] Anggaran")

                    except Exception as e:
                        gagal_proses.append(f"[{kode}] Error: {e}")

                    progress.progress((i + 1) / len(selected_mitigasi), text=f"📦 Memproses {i + 1} dari {len(selected_mitigasi)} mitigasi...")

                # Simpan hasil akhir
                st.session_state["detail_mitigasi"] = {
                    "Mitigasi": all_deskripsi,
                    "AnggaranPIC": all_anggaran
                }

                if all_deskripsi:
                    st.session_state["copy_tabel_deskripsi_mitigasi"] = pd.DataFrame(all_deskripsi)
                if all_anggaran:
                    st.session_state["copy_tabel_anggaran_pic"] = pd.DataFrame(all_anggaran)

                st.success("✅ Proses selesai!")

                if gagal_proses:
                    st.warning("⚠️ Beberapa item gagal diproses:")
                    for g in gagal_proses:
                        st.markdown(f"- {g}")


    
    # ✅ Blok aman untuk menampilkan Tabel Deskripsi Mitigasi dan Anggaran & PIC
    detail_mitigasi = st.session_state.get("detail_mitigasi", {})

    # Tabel Deskripsi Mitigasi
    df_mitigasi = pd.DataFrame(detail_mitigasi.get("Mitigasi", []))
    if not df_mitigasi.empty:
        st.subheader("📌 Tabel Deskripsi Mitigasi (silahkan edit)")
        if "No" not in df_mitigasi.columns:
            df_mitigasi.insert(0, "No", range(1, len(df_mitigasi) + 1))
        if "Kode Risiko" in df_mitigasi.columns:
            ordered_cols = ["No", "Kode Risiko"] + [col for col in df_mitigasi.columns if col not in ["No", "Kode Risiko"]]
            df_mitigasi = df_mitigasi[ordered_cols]
        st.data_editor(df_mitigasi, hide_index=True, use_container_width=True, num_rows="dynamic")

    # Tabel Anggaran & PIC
    df_anggaran = pd.DataFrame(detail_mitigasi.get("AnggaranPIC", []))
    if not df_anggaran.empty:
        st.subheader("📌 Tabel Anggaran & PIC (silahkan edit)")
        if "No" not in df_anggaran.columns:
            df_anggaran.insert(0, "No", range(1, len(df_anggaran) + 1))

        df_anggaran = df_anggaran[["No", "Kode Risiko"] + [col for col in df_anggaran.columns if col not in ["No", "Kode Risiko"]]]

        edited_df_anggaran = st.data_editor(
            df_anggaran,
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_anggaran"
        )

        # Sebelum tombol simpan, pastikan data sudah tersalin ke session_state
        if not df_mitigasi.empty:
            st.session_state["copy_tabel_deskripsi_mitigasi"] = df_mitigasi

        if not df_anggaran.empty:
            st.session_state["copy_tabel_anggaran_pic"] = df_anggaran

            # Hitung otomatis setiap kali df_anggaran berubah
            total_biaya, formatted_total = hitung_total_biaya_perlakuan(df_anggaran)
            st.info(f"💰 Total Biaya Perlakuan Risiko (otomatis): Rp {formatted_total}")

        
        if st.button("🔄 Update Data"):
            update_copy_tables()


        save_updated_data_to_excel()


    
if __name__ == "__main__":
    main()
