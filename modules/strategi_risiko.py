import streamlit as st
import pandas as pd
import os
import tempfile
import re
import openai
import json
import uuid  # Gunakan UUID untuk key unik
from datetime import datetime
from modules.utils import get_user_file
import io  # untuk writer BytesIO

# ============== Taksonomi Risiko (BARU) ==============
TAXONOMY = {
    "🧭 Strategic Risk": [
        "Kegagalan Pelaksanaan Inisiatif Strategis Pengembangan Bisnis",
        "Kegagalan Penyesuaian Tarif Jasa Kepelabuhanan",
        "Perubahan Iklim (Pemanasan Global)",
    ],
    "📈 Market Risk": [
        "Penurunan Throughput Petikemas",
        "Rugi Selisih Kurs",
    ],
    "💰 Financial Risk": [
        "Peningkatan Beban Keuangan",
        "Denda/Kurang Bayar Pajak",
        "Inefisiensi Biaya",
    ],
    "🖥️ Operational Risk": [
        "Cyber Attack Sistem Informasi",
        "Ketidaksiapan Fasilitas dan/atau Peralatan Operasi",
        "Kecelakaan Kerja pada Karyawan Perusahaan",
        "Penurunan Trafik Kapal",
        "Penurunan Throughput Non-Petikemas",
        "Tidak Optimalnya Pengelolaan Aset Idle",
        "Gangguan Layanan Akibat Faktor Eksternal (Alam/Sosial)",
        "Ketidaksesuaian Kualifikasi Pekerja",
    ],
    "🏗️ Investment / Project Risk": [
        "Ketidaksesuaian Target Pelaksanaan Investasi Strategis",
    ],
    "⚖️ Regulatory, Legal & Compliance Risk": [
        "Pelanggaran Regulasi/Kontrak Kerjasama",
    ],
    "🌐 Reputational Risk": [
        "Fraud, Penyuapan, dan Gratifikasi",
    ],
}

# ============== Helper: ekstrak JSON dari teks ==============
def extract_json(response_text):
    try:
        json_pattern = re.compile(r'\[.*\]', re.DOTALL)
        json_match = json_pattern.search(response_text)
        if json_match:
            json_data = json_match.group()
            return json.loads(json_data)
        else:
            return None
    except json.JSONDecodeError:
        return None

# ============== Inisialisasi data default ==============
def initialize_data():
    if "ambang_batas" not in st.session_state:
        default_ambang = pd.DataFrame({
            "Ambang Batas": [
                "Total Aset",
                "Nilai risk capacity",
                "Nilai risk appetite",
                "Nilai risk tolerance",
                "Nilai limit risiko"
            ],
            "Input Pengguna": ["", "", "", "", ""]
        })
        st.session_state["ambang_batas"] = default_ambang.copy()
        st.session_state["ambang_batas_temp"] = default_ambang.copy()

# ============== Perhitungan Ambang Batas ==============
def modul_ambang_batas(total_aset):
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

# ============== Generator Kode Risiko (fallback jika GPT tidak memberi) ==============
def generate_risk_codes(df):
    if "Kode Risiko" not in df.columns:
        df["Kode Risiko"] = ""
    for idx, row in df.iterrows():
        if not row["Kode Risiko"]:
            kategori = row.get("Kategori Risiko T2 & T3 KBUMN", "GEN")
            prefix = re.sub(r'[^A-Za-z]', '', kategori[:3]).upper() or "GEN"
            df.at[idx, "Kode Risiko"] = f"RISK-{prefix}-{idx+1}"
    return df

# ============== Editor Metrix Strategi Risiko ==============
def modul_metrix_strategi_risiko():
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
        st.session_state["metrix_strategi"] = edited_metrix.copy()
        st.session_state["copy_metrix_strategi_risiko"] = edited_metrix.copy()
        st.session_state["metrix_strategi"] = generate_risk_codes(st.session_state["metrix_strategi"])
        st.success("✅ Data pada 'Metrix Strategi Risiko' berhasil diperbarui & disalin.")

# ============== PEMILIHAN TAKSONOMI (BARU, MULTISELECT) ==============
def tampilkan_taksonomi_risiko_relevan():
    st.subheader("Taksonomi Risiko 📝")
    with st.expander("**Taksonomi Risiko Relevan**", expanded=True):
        st.write("Pilih beberapa item risiko per kategori:")

        # state awal
        if "selected_taxonomi" not in st.session_state:
            st.session_state["selected_taxonomi"] = []  # list of dict: {"kategori": "...", "risiko": "..."}

        # bangun dict -> set untuk memudahkan cek selected
        current = st.session_state["selected_taxonomi"]
        selected_set = {(d["kategori"], d["risiko"]) for d in current if isinstance(d, dict)}

        new_selection = set(selected_set)

        for category, items in TAXONOMY.items():
            st.markdown(f"**{category}**")
            chosen = st.multiselect(
                f"Pilih item untuk {category}",
                options=items,
                default=[r for (cat, r) in selected_set if cat == category],
                key=f"ms_{re.sub(r'[^A-Za-z0-9]', '_', category)}"
            )
            # tambahkan yang dipilih
            for r in chosen:
                new_selection.add((category, r))
            # hapus yang tidak dipilih
            for r in [r0 for (cat0, r0) in list(new_selection) if cat0 == category and r0 not in chosen]:
                new_selection.discard((category, r))

        # simpan balik ke session_state
        st.session_state["selected_taxonomi"] = [{"kategori": c, "risiko": r} for (c, r) in sorted(new_selection)]

        if st.button("✅ Simpan Pilihan", key="update_taxonomy_selection"):
            st.success("✅ Pilihan Taksonomi Risiko berhasil diperbarui!")

        st.write("---")
        chosen_list = st.session_state["selected_taxonomi"]
        if chosen_list:
            st.write("Anda telah memilih:")
            for i, d in enumerate(chosen_list, start=1):
                st.write(f"{i}. {d['kategori']} — {d['risiko']}")
        else:
            st.write("Belum ada pilihan.")

        return TAXONOMY

# ============== OpenAI helper ==============
def get_gpt_response(prompt, system_message="", model="gpt-4", temperature=0.7, max_tokens=2000):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ Error saat menghubungi GPT: {e}"

# ============== Saran AI: Metrix Strategi Risiko (mengacu taksonomi baru) ==============
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

            # Siapkan payload yang jelas untuk GPT
            # Kami minta GPT mengisi Metrix untuk SETIAP item yang dipilih:
            # - Kategori Risiko T2 & T3 KBUMN: di-set SAMA DENGAN kategori yang dipilih user
            # - (Opsional) GPT boleh turunkan parameter dari 'risiko' (nama risiko)
            payload = {
                "risks_selected": selected_taxonomies,  # [{"kategori": "...", "risiko": "..."}]
                "expected_columns": [
                    "Kode Risiko",
                    "Kategori Risiko T2 & T3 KBUMN",
                    "Risk Appetite Statement",
                    "Sikap Terhadap Risiko",
                    "Parameter",
                    "Satuan Ukuran",
                    "Nilai Batasan/Limit"
                ],
                "notes": "Set 'Kategori Risiko T2 & T3 KBUMN' persis sama dengan field 'kategori' dari input."
            }

            prompt = f"""
Berikut ini daftar item risiko yang dipilih pengguna (format JSON):
{json.dumps(payload, indent=2, ensure_ascii=False)}

TUGAS ANDA:
- Wajib keluarkan satu baris untuk SETIAP item risiko yang dipilih.
- Balas HANYA dengan JSON array valid, tanpa teks tambahan di luar JSON.
- JSON array berisi objek-objek dengan kolom persis:
  - "Kode Risiko" (boleh kosong, akan diisi sistem jika tidak ada)
  - "Kategori Risiko T2 & T3 KBUMN" (ISI DENGAN NILAI 'kategori' dari input)
  - "Risk Appetite Statement"
  - "Sikap Terhadap Risiko" (hanya boleh: "Strategis", "Moderat", "Konservatif", "Tidak toleran")
  - "Parameter"
  - "Satuan Ukuran"
  - "Nilai Batasan/Limit"
- Gunakan nilai 'risiko' dari input untuk menginspirasi 'Risk Appetite Statement' dan 'Parameter'.
- Pastikan struktur JSON valid.
"""

            progress.progress(0.45, "🧠 Menghubungi GPT...")
            ai_text = get_gpt_response(
                prompt,
                system_message="Anda adalah asisten AI yang membantu analisis risiko untuk perusahaan pelabuhan.",
                temperature=0.4,
                max_tokens=4000
            )

            progress.progress(0.65, "📥 Parsing respons AI...")
            recommended_data = extract_json(ai_text)
            if not recommended_data:
                raise ValueError("Respons AI tidak valid atau tidak mengandung JSON.")

            expected_columns = [
                "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN",
                "Risk Appetite Statement", "Sikap Terhadap Risiko",
                "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
            ]

            df_recommended = pd.DataFrame.from_records(recommended_data)

            missing_cols = [col for col in expected_columns if col not in df_recommended.columns]
            if missing_cols:
                raise ValueError(f"Kolom berikut tidak ditemukan dalam hasil AI: {missing_cols}")

            valid_attitudes = ["Strategis", "Moderat", "Konservatif", "Tidak toleran"]
            df_recommended["Sikap Terhadap Risiko"] = df_recommended["Sikap Terhadap Risiko"].apply(
                lambda x: x if x in valid_attitudes else "Moderat"
            )

            df_recommended = df_recommended.reset_index(drop=True)

            progress.progress(0.85, "💾 Menyimpan hasil ke session_state...")

            st.session_state["metrix_strategi"] = df_recommended.copy()
            st.session_state["temp_metrix_strategi_risiko"] = df_recommended.copy()
            st.session_state["copy_metrix_strategi_risiko"] = df_recommended.copy()

            # Fallback pengisian Kode Risiko bila kosong
            st.session_state["metrix_strategi"] = generate_risk_codes(st.session_state["metrix_strategi"])
            st.session_state["copy_metrix_strategi_risiko"] = st.session_state["metrix_strategi"].copy()

            progress.progress(1.0, "✅ Selesai!")
            st.success("✅ Saran AI berhasil ditambahkan & disalin ke session state.")

        except (json.JSONDecodeError, ValueError) as ve:
            st.error(f"⚠️ Format output AI tidak valid: {ve}")
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat menghubungi AI: {e}")

# ============== Simpan & Unduh gabungan Strategi Risiko ==============
def save_and_download_strategi_risiko_combined():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    kode_perusahaan = st.session_state.get("kode_perusahaan", "Unknown")
    folder_path = "C:/saved"
    os.makedirs(folder_path, exist_ok=True)

    nama_file = f"Strategi_Risiko_{kode_perusahaan}_{timestamp}.xlsx"
    server_file_path = os.path.join(folder_path, nama_file)

    df_copy_ambang = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame())
    limit_value = st.session_state.get("copy_limit_risiko", "-")
    df_limit = pd.DataFrame([{"Limit Risiko": limit_value}])
    df_metrix_copy = st.session_state.get("copy_metrix_strategi_risiko", pd.DataFrame())

    output = io.BytesIO()

    try:
        with pd.ExcelWriter(server_file_path, engine="xlsxwriter") as writer_server, \
             pd.ExcelWriter(output, engine="xlsxwriter") as writer_download:

            df_copy_ambang.to_excel(writer_server, sheet_name="Copy Ambang Batas Risiko", index=False)
            df_limit.to_excel(writer_server, sheet_name="Copy Limit Risiko", index=False)
            df_metrix_copy.to_excel(writer_server, sheet_name="Copy Metrix Strategi Risiko", index=False)

            df_copy_ambang.to_excel(writer_download, sheet_name="Copy Ambang Batas Risiko", index=False)
            df_limit.to_excel(writer_download, sheet_name="Copy Limit Risiko", index=False)
            df_metrix_copy.to_excel(writer_download, sheet_name="Copy Metrix Strategi Risiko", index=False)

        output.seek(0)
        st.success(f"✅ File berhasil disimpan ke server: `{server_file_path}`")

        st.download_button(
            label="⬇️ Unduh Strategi Risiko",
            data=output,
            file_name=nama_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Gagal menyimpan file: {e}")

# ============== MAIN APP ==============
def main():
    st.title("📊 Strategi Risiko - Upload & Analisa Data")

    uploaded_file = st.file_uploader("📥 Pilih file Excel", type=["xls", "xlsx"], key="data_uploader")

    st.session_state.setdefault("ambang_batas", pd.DataFrame(columns=["Ambang Batas", "Nilai"]))
    st.session_state.setdefault("metrix_strategi", pd.DataFrame(columns=[
        "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN", "Risk Appetite Statement",
        "Sikap Terhadap Risiko", "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
    ]))
    st.session_state.setdefault("copy_ambang_batas_risiko", {})
    st.session_state.setdefault("copy_limit_risiko", "-")
    st.session_state.setdefault("copy_metrix_strategi_risiko", pd.DataFrame())
    st.session_state.setdefault("kode_perusahaan", "Unknown")

    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file, engine="openpyxl")
            sheet_names = [sheet.strip() for sheet in xls.sheet_names]

            expected_strategi_sheets = [
                "Copy Ambang Batas Risiko",
                "Copy Limit Risiko",
                "Copy Metrix Strategi Risiko"
            ]

            profil_sheets = []
            strategi_sheets_found = []

            for sheet in sheet_names:
                if sheet in expected_strategi_sheets:
                    strategi_sheets_found.append(sheet)
                else:
                    profil_sheets.append(sheet)

            if profil_sheets:
                profil_data = {}
                for sheet in profil_sheets:
                    df = xls.parse(sheet)
                    sheet_key = sheet.lower().replace(" ", "_")
                    profil_data[sheet_key] = df.copy()

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
                st.session_state["copy_metrix_strategi_risiko"] = df_metrix
                st.session_state["metrix_strategi"] = df_metrix.copy()

            if strategi_sheets_found:
                st.success(f"✅ Data Strategi Risiko berhasil dimuat ({len(strategi_sheets_found)} sheet).")

            total_known_sheets = profil_sheets + strategi_sheets_found
            unknown_sheets = [s for s in sheet_names if s not in total_known_sheets]

            if unknown_sheets:
                st.warning(f"⚠️ Sheet berikut **tidak dikenali** dan tidak diproses: {', '.join(unknown_sheets)}")

        except Exception as e:
            st.error(f"❌ Gagal memuat data: {e}")

    profil_perusahaan = st.session_state.get("copy2_profil_perusahaan", {})
    informasi_perusahaan_df = profil_perusahaan.get("informasi_perusahaan", pd.DataFrame())

    total_aset_dari_profil = None
    with st.expander("🏢 Profil Perusahaan (Hasil Upload)", expanded=False):
        if not informasi_perusahaan_df.empty:
            try:
                kode_row = informasi_perusahaan_df[
                    informasi_perusahaan_df["Data yang dibutuhkan"].str.contains("Kode Perusahaan", case=False, na=False)
                ]
                aset_row = informasi_perusahaan_df[
                    informasi_perusahaan_df["Data yang dibutuhkan"].str.contains("Total Aset", case=False, na=False)
                ]

                if not kode_row.empty:
                    kode_perusahaan = kode_row.iloc[0]["Input Pengguna"]
                    st.session_state["kode_perusahaan"] = kode_perusahaan

                if not aset_row.empty:
                    total_aset_value = aset_row.iloc[0]["Input Pengguna"]
                    if str(total_aset_value).replace(".", "").replace(",", "").isdigit():
                        total_aset_dari_profil = int(str(total_aset_value).replace(".", "").replace(",", ""))
            except Exception as e:
                st.warning(f"⚠️ Ada masalah membaca data profil perusahaan: {e}")

            for idx, row in informasi_perusahaan_df.iterrows():
                kolom_data = str(row.get("Data yang dibutuhkan", "")).strip()
                kolom_input = str(row.get("Input Pengguna", "")).strip()
                st.markdown(f"**{kolom_data}**: {kolom_input}")
        else:
            st.warning("⚠️ Profil perusahaan belum dimuat atau kosong.")

    st.subheader("💰 Input Total Aset")
    if total_aset_dari_profil is not None:
        total_aset_input = st.text_input("Total Aset (diambil dari Profil Perusahaan):", value=str(total_aset_dari_profil))
    else:
        total_aset_input = st.text_input("Total Aset:", value="", placeholder="Contoh: 13000000000000")

    if str(total_aset_input).replace(".", "").replace(",", "").isdigit():
        total_aset = int(str(total_aset_input).replace(".", "").replace(",", ""))
    else:
        total_aset = None

    st.write("### 📊 Ambang Batas Risiko")
    df_ambang = pd.DataFrame.from_dict(
        st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame())
    )

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
                    except:
                        st.session_state["copy_limit_risiko"] = nilai_limit

                st.success("✅ Data Ambang Batas Risiko berhasil diperbarui.")
            else:
                st.warning("⚠️ Belum ada data untuk disalin.")

    with col2:
        if st.button("📊 Hitung Ambang Batas"):
            try:
                cleaned_input = str(total_aset_input).replace(".", "").replace(",", "").strip()
                total_aset_calc = int(cleaned_input)
                st.write(f"🔎 Total Aset digunakan untuk perhitungan: `{total_aset_calc:,}`")
            except (ValueError, TypeError):
                total_aset_calc = None
                st.error("❌ Total Aset tidak valid. Mohon masukkan angka yang benar.")

            if total_aset_calc:
                hasil_perhitungan, limit_risk = modul_ambang_batas(total_aset_calc)
                if hasil_perhitungan is not None and limit_risk is not None:
                    try:
                        df_edit = st.session_state["editor_ambang_batas"]
                        if "Ambang Batas" not in df_edit.columns:
                            df_edit = df_ambang[["Ambang Batas"]].copy()
                            df_edit["Nilai"] = st.session_state["editor_ambang_batas"]["Nilai"]

                        for idx, row in hasil_perhitungan.iterrows():
                            ambang = row["Ambang Batas"]
                            if ambang in df_edit["Ambang Batas"].values:
                                nilai_edit = df_edit.loc[df_edit["Ambang Batas"] == ambang, "Nilai"].values[0]
                                hasil_perhitungan.at[idx, "Nilai"] = nilai_edit
                    except Exception:
                        st.warning("⚠silahkan tekan update untuk melihat perubahan")

                    st.session_state["copy_ambang_batas_risiko"] = hasil_perhitungan.copy()
                    st.session_state["copy_limit_risiko"] = limit_risk
                    st.success("✅ Ambang Batas berhasil dihitung dan digabung dengan editan pengguna.")
                else:
                    st.warning("⚠️ Perhitungan gagal. Total aset tidak valid atau nol.")

    st.markdown("### 📌 Tabel Ambang Batas Risiko (Final)")
    df_final = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame()).copy()
    if isinstance(df_final, pd.DataFrame) and not df_final.empty:
        df_final = df_final.reset_index(drop=True)
        st.dataframe(df_final, hide_index=True)
    else:
        st.info("📭 Belum ada data ambang batas risiko yang dimuat atau dihitung.\n\nSilakan isi data secara manual atau gunakan tombol **Hitung Ambang Batas**.")

    if st.button("📋 Simpan Ulang dari Tabel Final"):
        if not edited_ambang_batas.empty:
            df_ambang.loc[:, "Nilai"] = edited_ambang_batas["Nilai"]
            st.session_state["copy_ambang_batas_risiko"] = df_ambang.drop(columns=["No"]).copy()
            baris_limit = df_ambang[df_ambang["Ambang Batas"] == "Limit Risiko"]
            if not baris_limit.empty:
                nilai_limit = baris_limit["Nilai"].values[0]
                try:
                    st.session_state["copy_limit_risiko"] = int(nilai_limit)
                except:
                    st.session_state["copy_limit_risiko"] = nilai_limit
            st.success("✅ Data Ambang Batas Risiko berhasil diperbarui.")
        else:
            st.warning("⚠️ Belum ada data untuk disalin.")

    # === Modul lanjutan ===
    tampilkan_taksonomi_risiko_relevan()
    saran_gpt_metrix_strategi_risiko()
    modul_metrix_strategi_risiko()

    save_and_download_strategi_risiko_combined()

# (Jika file ini dieksekusi langsung)
if __name__ == "__main__":
    main()
