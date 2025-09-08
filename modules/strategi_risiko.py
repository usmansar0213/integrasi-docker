import streamlit as st
import pandas as pd
import os
import io
import re
import json
import openai
from datetime import datetime

# --- Fungsi Global ---

def extract_json(response_text):
    """
    Mengekstrak blok JSON array valid dari teks respons.
    Fungsi ini lebih tangguh dengan mencari indeks awal dan akhir dari array JSON
    untuk mengabaikan teks tambahan di sekitar output AI.
    """
    try:
        start_index = response_text.find('[')
        end_index = response_text.rfind(']')

        if start_index != -1 and end_index != -1 and start_index < end_index:
            json_data = response_text[start_index : end_index + 1]
            return json.loads(json_data)
        else:
            st.error("❌ Tidak menemukan blok JSON yang valid dalam respons.")
            return None
    except json.JSONDecodeError as e:
        st.error(f"❌ Gagal memparsing JSON: {e}")
        st.error(f"❌ Teks yang gagal diparse: {response_text}")
        return None

def initialize_data():
    """Inisialisasi data ke dalam session state jika belum ada"""
    if "ambang_batas" not in st.session_state:
        default_ambang = pd.DataFrame({
            "Ambang Batas": [
                "Total Aset", "Nilai risk capacity", "Nilai risk appetite",
                "Nilai risk tolerance", "Nilai limit risiko"
            ],
            "Input Pengguna": ["", "", "", "", ""]
        })
        st.session_state["ambang_batas"] = default_ambang.copy()

    if "ambang_batas_temp" not in st.session_state:
        st.session_state["ambang_batas_temp"] = st.session_state["ambang_batas"].copy()

    if "metrix_strategi" not in st.session_state:
        st.session_state["metrix_strategi"] = pd.DataFrame(columns=[
            "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN", "Risk Appetite Statement",
            "Sikap Terhadap Risiko", "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
        ])

    st.session_state.setdefault("copy_ambang_batas_risiko", pd.DataFrame())
    st.session_state.setdefault("copy_limit_risiko", "-")
    st.session_state.setdefault("copy_metrix_strategi_risiko", pd.DataFrame())
    st.session_state.setdefault("kode_perusahaan", "Unknown")
    st.session_state.setdefault("selected_taxonomi", [])


def modul_ambang_batas(total_aset):
    """Menghitung ambang batas risiko berdasarkan total aset."""
    if total_aset is None or total_aset <= 0:
        return None, None

    risk_capacity = int(total_aset * 0.15)
    risk_appetite = int(0.3 * risk_capacity)
    risk_tolerance = int(0.4 * risk_capacity)
    limit_risk = int(0.2 * risk_capacity)

    hasil_perhitungan = pd.DataFrame({
        "Ambang Batas": [
            "Total Aset", "Risk Capacity", "Risk Appetite",
            "Risk Tolerance", "Limit Risiko"
        ],
        "Nilai": [total_aset, risk_capacity, risk_appetite, risk_tolerance, limit_risk],
        "Rumus Perhitungan": [
            "-",
            "15% dari Total Aset",
            "30% dari Risk Capacity",
            "40% dari Risk Capacity",
            "20% dari Risk Capacity"
        ]
    })
    
    return hasil_perhitungan, limit_risk


def generate_risk_codes(df):
    """Menghasilkan kode risiko unik berdasarkan kategori risiko jika belum ada."""
    if "Kode Risiko" not in df.columns:
        df["Kode Risiko"] = ""

    for idx, row in df.iterrows():
        if not row["Kode Risiko"] or pd.isna(row["Kode Risiko"]) or row["Kode Risiko"] == "":
            kategori = row.get("Kategori Risiko T2 & T3 KBUMN", "GEN")
            kode_risiko_baru = f"RISK-{kategori[:3].upper()}-{idx+1}"
            df.at[idx, "Kode Risiko"] = kode_risiko_baru
    return df
    
def modul_metrix_strategi_risiko():
    # --- METRIX STRATEGI RISIKO ---
    st.subheader("Modul Metrix Strategi Risiko 📝")

    if "Kode Risiko" not in st.session_state["metrix_strategi"].columns:
        st.session_state["metrix_strategi"]["Kode Risiko"] = ""

    df_metrix_display = st.session_state["metrix_strategi"][[
        "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN",
        "Risk Appetite Statement", "Sikap Terhadap Risiko",
        "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
    ]].copy()

    df_metrix_display.insert(0, "No", range(1, len(df_metrix_display) + 1))

    edited_metrix = st.data_editor(
        df_metrix_display,
        key="metrix_strategi_editor",
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("🔄 Update Data", key="update_metrix_strategi"):
        if "No" in edited_metrix.columns:
            edited_metrix = edited_metrix.drop(columns=["No"])
        
        st.session_state["metrix_strategi"] = edited_metrix.copy()
        st.session_state["copy_metrix_strategi_risiko"] = edited_metrix.copy()
        st.session_state["metrix_strategi"] = generate_risk_codes(st.session_state["metrix_strategi"])
        st.success("✅ Data pada 'Metrix Strategi Risiko' berhasil diperbarui & disalin.")

def tampilkan_taksonomi_risiko_relevan():
    st.subheader("Taksonomi Risiko 📝")
    with st.expander("**Taksonomi Risiko Relevan**", expanded=True):
        st.write("Pilih Taksonomi Risiko Relevan:")

        taxonomy = {
            "1.1 Kategori Risiko Fiskal": [
                {"kode": "1.1.1", "nama": "Peristiwa Risiko terkait Dividen"},
                {"kode": "1.1.2", "nama": "Peristiwa Risiko terkait PMN"},
                {"kode": "1.1.3", "nama": "Peristiwa Risiko terkait Subsidi & Kompensasi"}
            ],
            "1.2 Kategori Risiko Kebijakan": [
                {"kode": "1.2.4", "nama": "Peristiwa Risiko terkait Kebijakan SDM"},
                {"kode": "1.2.5", "nama": "Peristiwa Risiko terkait Kebijakan Sektoral"}
            ],
            "1.3 Kategori Risiko Komposisi": [
                {"kode": "1.3.6", "nama": "Peristiwa Risiko terkait Konsentrasi Portofolio"}
            ],
            "2.4 Kategori Risiko Struktur": [
                {"kode": "2.4.7", "nama": "Peristiwa Risiko terkait Struktur Korporasi"}
            ],
            "2.5 Kategori Risiko Restrukturisasi dan Reorganisasi": [
                {"kode": "2.5.8", "nama": "Peristiwa Risiko terkait M&A, JV, Restrukturisasi"}
            ],
            "3.6 Kategori Risiko Industri Umum": [
                {"kode": "3.6.9", "nama": "Peristiwa Risiko terkait Formulasi Strategis"},
                {"kode": "3.6.10", "nama": "Peristiwa Risiko terkait Pasar & Makroekonomi (Observasi 6)"},
                {"kode": "3.6.11", "nama": "Peristiwa Risiko terkait Hukum, Reputasi & Kepatuhan (Observasi 15)"},
                {"kode": "3.6.12", "nama": "Peristiwa Risiko terkait Keuangan"},
                {"kode": "3.6.13", "nama": "Peristiwa Risiko terkait Proyek (Observasi 8)"},
                {"kode": "3.6.14", "nama": "Peristiwa Risiko terkait Teknologi Informasi & Keamanan Siber (Observasi 12)"},
                {"kode": "3.6.15", "nama": "Peristiwa Risiko terkait Sosial & Lingkungan"},
                {"kode": "3.6.16", "nama": "Peristiwa Risiko terkait Operasional (Observasi 2-5, 13,16, 17)"}
            ],
            "3.7 Kategori Risiko Industri Perbankan": [],
            "3.8 Kategori Risiko Industri Asuransi": []
        }
        
        selected = st.session_state["selected_taxonomi"]
        new_selection = []

        for category, items in taxonomy.items():
            st.markdown(f"**{category}**")
            for item in items:
                unique_key = f"chk_{category.replace(' ', '_')}_{item['kode']}"
                is_checked = any(sel.get("kode") == item["kode"] for sel in selected)
                checked = st.checkbox(f"{item['kode']} - {item['nama']}", key=unique_key, value=is_checked)
                
                if checked:
                    if item not in new_selection:
                        new_selection.append(item)
                else:
                    new_selection = [sel for sel in new_selection if sel["kode"] != item["kode"]]
        
        if st.button("✅ Simpan Pilihan", key="update_taxonomy_selection"):
            st.session_state["selected_taxonomi"] = new_selection
            st.success("✅ Pilihan Taksonomi Risiko berhasil diperbarui!")

        st.write("---")
        st.write("Anda telah memilih:")
        if new_selection:
            for idx, item in enumerate(new_selection, start=1):
                st.write(f"{idx}. {item['kode']} - {item['nama']}")
        else:
            st.write("Belum ada pilihan.")
        
        return taxonomy


def get_gpt_response(prompt, system_message="", model="gpt-4", temperature=0.7, max_tokens=2000):
    """Mengirim prompt ke OpenAI GPT API dan mengembalikan respons."""
    try:
        if "OPENAI_API_KEY" not in os.environ:
            st.error("❌ Kunci API OpenAI tidak ditemukan. Pastikan sudah diatur di environment.")
            return "Error: OPENAI_API_KEY tidak ditemukan."

        openai.api_key = os.environ["OPENAI_API_KEY"]
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error saat menghubungi GPT: {e}"


def saran_gpt_metrix_strategi_risiko():
    st.markdown("### 🤖 Saran AI: Metrix Strategi Risiko")

    selected_taxonomies = st.session_state.get("selected_taxonomi", [])
    if not selected_taxonomies:
        st.warning("⚠️ Anda belum memilih taksonomi risiko. Pilih taksonomi terlebih dahulu.")
        return

    if st.button("🔍 Dapatkan Saran AI"):
        progress = st.progress(0, text="📡 Menyiapkan permintaan ke AI...")

        try:
            progress.progress(0.2, "📄 Menyusun prompt...")
            prompt = f"""
            Berikut adalah daftar kategori risiko yang telah dipilih pengguna:

            {json.dumps(selected_taxonomies, indent=4)}

            **Tugas Anda:**
            - WAJIB memberikan output untuk setiap kategori risiko yang diberikan.
            - TIDAK BOLEH menghilangkan satu pun.
            - Hanya balas dalam bentuk JSON array `[{{...}}, {{...}}]`.
            - Tanpa teks tambahan di luar JSON.
            - Kolom yang harus disediakan:
                - "Kode Risiko"
                - "Kategori Risiko T2 & T3 KBUMN"
                - "Risk Appetite Statement"
                - "Sikap Terhadap Risiko" (hanya: "Strategis", "Moderat", "Konservatif", "Tidak toleran")
                - "Parameter"
                - "Satuan Ukuran"
                - "Nilai Batasan/Limit"
            - Jika tidak yakin terhadap isian, buat isian terbaik berdasarkan logika umum.
            - Pastikan struktur JSON valid.
            - Jangan ada pembuka atau penutup kalimat, hanya JSON murni.
            """

            progress.progress(0.4, "🧠 Menghubungi GPT...")
            ai_text = get_gpt_response(
                prompt,
                system_message="Anda adalah asisten AI yang membantu analisis risiko.",
                temperature=0.5,
                max_tokens=4000
            )

            progress.progress(0.6, "📥 Parsing respons AI...")
            recommended_data = extract_json(ai_text)
            if not recommended_data:
                raise ValueError("Respons AI tidak valid atau tidak mengandung JSON.")

            expected_columns = [
                "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN",
                "Risk Appetite Statement", "Sikap Terhadap Risiko",
                "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
            ]

            df_recommended = pd.DataFrame.from_records(recommended_data)

            # Cek kolom wajib
            missing_cols = [col for col in expected_columns if col not in df_recommended.columns]
            if missing_cols:
                raise ValueError(f"Kolom berikut tidak ditemukan dalam hasil AI: {missing_cols}")

            # Validasi nilai kolom 'Sikap Terhadap Risiko'
            valid_attitudes = ["Strategis", "Moderat", "Konservatif", "Tidak toleran"]
            df_recommended["Sikap Terhadap Risiko"] = df_recommended["Sikap Terhadap Risiko"].apply(
                lambda x: x if x in valid_attitudes else "Moderat"
            )

            df_recommended = df_recommended.reset_index(drop=True)

            progress.progress(0.85, "💾 Menyimpan hasil ke session_state...")

            st.session_state["metrix_strategi"] = df_recommended.copy()
            st.session_state["temp_metrix_strategi_risiko"] = df_recommended.copy()
            st.session_state["copy_metrix_strategi_risiko"] = df_recommended.copy()

            progress.progress(1.0, "✅ Selesai!")
            st.success("✅ Saran AI berhasil ditambahkan dan disalin ke session state.")

        except (json.JSONDecodeError, ValueError) as ve:
            st.error(f"⚠️ Format output AI tidak valid: {ve}")
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat menghubungi AI: {e}")

def save_and_download_strategi_risiko_combined():
    """Menggabungkan data dan menyediakan tombol unduh."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    kode_perusahaan = st.session_state.get("kode_perusahaan", "Unknown")
    nama_file = f"Strategi_Risiko_{kode_perusahaan}_{timestamp}.xlsx"

    df_ambang = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame())
    df_metrix = st.session_state.get("copy_metrix_strategi_risiko", pd.DataFrame())

    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer_download:
            if not df_ambang.empty:
                df_ambang.to_excel(writer_download, sheet_name="Ambang Batas Risiko", index=False)
            if not df_metrix.empty:
                df_metrix.to_excel(writer_download, sheet_name="Metrix Strategi Risiko", index=False)

        output.seek(0)
        st.success("✅ File berhasil dibuat.")
        st.download_button(
            label="⬇️ Unduh Strategi Risiko",
            data=output,
            file_name=nama_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"❌ Gagal membuat file: {e}")


def main():
    st.title("📊 Strategi Risiko - Upload & Analisa Data")
    initialize_data()

    uploaded_file = st.file_uploader("📥 Silahkan Load file Profil Perusahaan", type=["xls", "xlsx"], key="data_uploader")

    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file, engine="openpyxl")
            sheet_names = [sheet.strip() for sheet in xls.sheet_names]

            expected_strategi_sheets = [
                "Copy Ambang Batas Risiko",
                "Copy Limit Risiko",
                "Copy Metrix Strategi Risiko"
            ]

            profil_sheets = [s for s in sheet_names if s not in expected_strategi_sheets]
            strategi_sheets_found = [s for s in sheet_names if s in expected_strategi_sheets]

            if profil_sheets:
                profil_data = {sheet.lower().replace(" ", "_"): xls.parse(sheet).copy() for sheet in profil_sheets}
                st.session_state["copy2_profil_perusahaan"] = profil_data
                st.success(f"✅ Data Profil Perusahaan berhasil dimuat ({len(profil_data)} tabel).")

            if "Copy Ambang Batas Risiko" in strategi_sheets_found:
                st.session_state["copy_ambang_batas_risiko"] = xls.parse("Copy Ambang Batas Risiko")
            if "Copy Limit Risiko" in strategi_sheets_found:
                df_limit = xls.parse("Copy Limit Risiko")
                if not df_limit.empty and "Limit Risiko" in df_limit.columns:
                    limit_value = df_limit["Limit Risiko"].iloc[0]
                    st.session_state["copy_limit_risiko"] = limit_value
                else:
                    st.warning("⚠️ Sheet 'Copy Limit Risiko' ditemukan, tapi format kolom tidak sesuai.")
            if "Copy Metrix Strategi Risiko" in strategi_sheets_found:
                df_metrix = xls.parse("Copy Metrix Strategi Risiko")
                st.session_state["copy_metrix_strategi_risiko"] = df_metrix.copy()
                st.session_state["metrix_strategi"] = df_metrix.copy()

            if strategi_sheets_found:
                st.success(f"✅ Data Strategi Risiko berhasil dimuat ({len(strategi_sheets_found)} sheet).")

            total_known_sheets = profil_sheets + strategi_sheets_found
            unknown_sheets = [s for s in sheet_names if s not in total_known_sheets]
            if unknown_sheets:
                st.warning(f"⚠️ Sheet berikut **tidak dikenali** dan tidak diproses: {', '.join(unknown_sheets)}")
        except Exception as e:
            st.error(f"❌ Gagal memuat data: {e}")

    # --- Tampilkan Profil Perusahaan (Hasil Upload) ---
    profil_perusahaan = st.session_state.get("copy2_profil_perusahaan", {})
    informasi_perusahaan_df = profil_perusahaan.get("informasi_perusahaan", pd.DataFrame())
    total_aset_dari_profil = None

    with st.expander("🏢 Profil Perusahaan (Hasil Upload)", expanded=False):
        if not informasi_perusahaan_df.empty:
            try:
                kode_row = informasi_perusahaan_df[informasi_perusahaan_df["Data yang dibutuhkan"].str.contains("Kode Perusahaan", case=False, na=False)]
                aset_row = informasi_perusahaan_df[informasi_perusahaan_df["Data yang dibutuhkan"].str.contains("Total Aset", case=False, na=False)]

                if not kode_row.empty:
                    st.session_state["kode_perusahaan"] = str(kode_row.iloc[0]["Input Pengguna"])
                if not aset_row.empty:
                    total_aset_value = aset_row.iloc[0]["Input Pengguna"]
                    if str(total_aset_value).replace(".", "").replace(",", "").isdigit():
                        total_aset_dari_profil = int(str(total_aset_value).replace(".", "").replace(",", ""))
            except Exception as e:
                st.warning(f"⚠️ Ada masalah membaca data profil perusahaan: {e}")

            for idx, row in informasi_perusahaan_df.iterrows():
                st.markdown(f"**{str(row.get('Data yang dibutuhkan', '')).strip()}**: {str(row.get('Input Pengguna', '')).strip()}")
        else:
            st.warning("⚠️ Profil perusahaan belum dimuat atau kosong.")

    # --- Input Manual atau Otomatis Total Aset ---
    st.subheader("💰 Input Total Aset")
    total_aset_input = st.text_input("Total Aset:", value=str(total_aset_dari_profil) if total_aset_dari_profil is not None else "", placeholder="Contoh: 13000000000000")

    if total_aset_input.isdigit():
        total_aset = int(total_aset_input)
    else:
        total_aset = None

    # --- Tampilkan tabel Ambang Batas Risiko ---
    st.write("### 📊 Ambang Batas Risiko")
    df_ambang = pd.DataFrame.from_dict(st.session_state.get("copy_ambang_batas_risiko", {}))

    if df_ambang.empty:
        df_ambang = pd.DataFrame({
            "Ambang Batas": [
                "Total Aset", "Risk Capacity", "Risk Appetite",
                "Risk Tolerance", "Limit Risiko"
            ],
            "Nilai": ["-", "-", "-", "-", "-"]
        })

    df_ambang = df_ambang.reset_index(drop=True)
    df_ambang.insert(0, "No", range(1, len(df_ambang) + 1))
    
    edited_ambang_batas = st.data_editor(
        df_ambang[["Ambang Batas", "Nilai"]],
        key="editor_ambang_batas",
        num_rows="fixed",
        hide_index=True
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Update Data"):
            if not edited_ambang_batas.empty:
                df_ambang.loc[:, "Nilai"] = edited_ambang_batas["Nilai"]
                st.session_state["copy_ambang_batas_risiko"] = df_ambang.drop(columns=["No"]).copy()
                baris_limit = df_ambang[df_ambang["Ambang Batas"] == "Limit Risiko"]
                if not baris_limit.empty:
                    nilai_limit = baris_limit["Nilai"].values[0]
                    try:
                        st.session_state["copy_limit_risiko"] = int(nilai_limit)
                    except (ValueError, TypeError):
                        st.session_state["copy_limit_risiko"] = nilai_limit
                st.success("✅ Data Ambang Batas Risiko berhasil diperbarui.")
            else:
                st.warning("⚠️ Belum ada data untuk disalin.")

    with col2:
        if st.button("📊 Hitung Ambang Batas"):
            try:
                cleaned_input = str(total_aset_input).replace(".", "").replace(",", "").strip()
                total_aset = int(cleaned_input)
                st.write(f"🔎 Total Aset digunakan untuk perhitungan: `{total_aset:,}`")
                
                hasil_perhitungan, limit_risk = modul_ambang_batas(total_aset)
                if hasil_perhitungan is not None and limit_risk is not None:
                    st.session_state["copy_ambang_batas_risiko"] = hasil_perhitungan.copy()
                    st.session_state["copy_limit_risiko"] = limit_risk
                    st.success("✅ Ambang Batas berhasil dihitung.")
                else:
                    st.warning("⚠️ Perhitungan gagal. Total aset tidak valid atau nol.")
            except (ValueError, TypeError):
                st.error("❌ Total Aset tidak valid. Mohon masukkan angka yang benar.")

    st.markdown("### 📌 Tabel Ambang Batas Risiko (Final)")
    df_final = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame()).copy()
    if isinstance(df_final, pd.DataFrame) and not df_final.empty:
        df_final = df_final.reset_index(drop=True)
        st.dataframe(df_final, hide_index=True)
    else:
        st.info("📭 Belum ada data ambang batas risiko yang dimuat atau dihitung.\n\nSilakan isi data secara manual atau gunakan tombol **Hitung Ambang Batas** untuk menghasilkan data otomatis berdasarkan total aset.")

    if st.button("📋 Simpan Ulang dari Tabel Final"):
        if not edited_ambang_batas.empty:
            df_ambang.loc[:, "Nilai"] = edited_ambang_batas["Nilai"]
            st.session_state["copy_ambang_batas_risiko"] = df_ambang.drop(columns=["No"]).copy()
            baris_limit = df_ambang[df_ambang["Ambang Batas"] == "Limit Risiko"]
            if not baris_limit.empty:
                nilai_limit = baris_limit["Nilai"].values[0]
                try:
                    st.session_state["copy_limit_risiko"] = int(nilai_limit)
                except (ValueError, TypeError):
                    st.session_state["copy_limit_risiko"] = nilai_limit
            st.success("✅ Data Ambang Batas Risiko berhasil diperbarui.")
        else:
            st.warning("⚠️ Belum ada data untuk disalin.")

    # --- Modul lanjutan ---
    tampilkan_taksonomi_risiko_relevan()
    saran_gpt_metrix_strategi_risiko()
    modul_metrix_strategi_risiko()
    save_and_download_strategi_risiko_combined()

if __name__ == "__main__":
    main()
