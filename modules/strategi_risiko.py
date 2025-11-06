import streamlit as st
import pandas as pd
import os
import tempfile
import re
import openai
import json
import uuid  # opsional
from datetime import datetime
# from modules.utils import get_user_file  # opsional bila ingin simpan per-user
import io
from collections import defaultdict

# =========================
# Helpers & Utilities
# =========================

def extract_json_robust(text: str):
    """
    Ambil JSON array valid dari text:
    - Bersihkan code-fence ``` / ```json
    - Coba parse keseluruhan teks dulu
    - Cari array pertama dengan bracket stack (lebih andal)
    - Fallback: jika hanya object {..}, bungkus ke dalam array
    Return: list (JSON array) atau None.
    """
    if text is None:
        return None

    # bersihkan code-fence
    cleaned = re.sub(r"```(?:json)?", "", str(text), flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()

    # 1) kalau seluruh teks sudah JSON array/object murni
    for candidate in (cleaned, cleaned.strip()):
        try:
            obj = json.loads(candidate)
            if isinstance(obj, list):
                return obj
            if isinstance(obj, dict):
                return [obj]
        except Exception:
            pass

    # 2) cari blok [ ... ] pertama dengan bracket stack
    s = cleaned
    start_idx = None
    stack = 0
    for i, ch in enumerate(s):
        if ch == '[':
            start_idx = i
            stack = 1
            break
    if start_idx is not None:
        for j in range(start_idx + 1, len(s)):
            if s[j] == '[':
                stack += 1
            elif s[j] == ']':
                stack -= 1
                if stack == 0:
                    snippet = s[start_idx:j+1]
                    try:
                        arr = json.loads(snippet)
                        if isinstance(arr, list):
                            return arr
                    except Exception:
                        pass
                    break  # hentikan pencarian utama

    # 3) fallback: cari object { ... } lalu bungkus
    obj_start = s.find('{')
    if obj_start != -1:
        stack = 0
        for j in range(obj_start, len(s)):
            if s[j] == '{':
                stack += 1
            elif s[j] == '}':
                stack -= 1
                if stack == 0:
                    snippet = s[obj_start:j+1]
                    try:
                        obj = json.loads(snippet)
                        if isinstance(obj, dict):
                            return [obj]
                    except Exception:
                        pass
                    break

    return None

def _to_int(s):
    """Parse '1.234.567' / '1,234,567' / '1 234' jadi int. Return None jika gagal."""
    if s is None:
        return None
    cleaned = re.sub(r"[^\d]", "", str(s))
    try:
        return int(cleaned) if cleaned else None
    except Exception:
        return None

def initialize_data():
    """Inisialisasi data ke session_state bila belum ada."""
    if "ambang_batas" not in st.session_state:
        default_ambang = pd.DataFrame({
            "Ambang Batas": [
                "Total Aset",
                "Risk Capacity",
                "Risk Appetite",
                "Risk Tolerance",
                "Limit Risiko"
            ],
            "Nilai": ["-", "-", "-", "-", "-"]
        })
        st.session_state["ambang_batas"] = default_ambang.copy()
        st.session_state["ambang_batas_temp"] = default_ambang.copy()

    st.session_state.setdefault("metrix_strategi", pd.DataFrame(columns=[
        "Kode Risiko",
        "Kategori Risiko T2 & T3 KBUMN",  # dipakai sbg kolom kompatibel, nilai berisi nama kategori Danantara
        "Risk Appetite Statement",
        "Sikap Terhadap Risiko",
        "Parameter",
        "Satuan Ukuran",
        "Nilai Batasan/Limit"
    ]))

    st.session_state.setdefault("copy_ambang_batas_risiko", pd.DataFrame())
    st.session_state.setdefault("copy_limit_risiko", "-")
    st.session_state.setdefault("copy_metrix_strategi_risiko", pd.DataFrame())
    st.session_state.setdefault("kode_perusahaan", "Unknown")
    st.session_state.setdefault("selected_taxonomi", [])

def modul_ambang_batas(total_aset: int):
    """Hitung ambang batas berbasis total aset (contoh rumus default)."""
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

def generate_risk_codes(df: pd.DataFrame):
    """
    Hasilkan kode risiko unik dan stabil per kategori (RISK-XXX-001).
    Menggunakan awalan dari kategori (3 huruf) + counter per kategori.
    """
    if "Kode Risiko" not in df.columns:
        df["Kode Risiko"] = ""

    counters = defaultdict(int)

    for i, row in df.iterrows():
        if not str(row.get("Kode Risiko", "")).strip():
            kategori = str(row.get("Kategori Risiko T2 & T3 KBUMN", "GEN")).strip()
            key = (kategori[:3].upper() if kategori else "GEN")
            if not key or not key[0].isalnum():
                key = "GEN"
            counters[key] += 1
            df.at[i, "Kode Risiko"] = f"RISK-{key}-{counters[key]:03d}"
    return df

# =========================
# Taksonomi (Danantara)
# =========================

DANANTARA_TAXONOMY = {
    "Danantara Risk Taxonomy": [
        {"kode": "DAN-01", "nama": "Strategic Risk"},
        {"kode": "DAN-02", "nama": "Market Risk"},
        {"kode": "DAN-03", "nama": "Financial Risk"},
        {"kode": "DAN-04", "nama": "Credit/Counterparty Risk"},
        {"kode": "DAN-05", "nama": "Operational Risk"},
        {"kode": "DAN-06", "nama": "Investment/Project Risk"},
        {"kode": "DAN-07", "nama": "Reputational Risk"},
        {"kode": "DAN-08", "nama": "Regulatory, Legal & Compliance Risk"},
    ]
}

def tampilkan_taksonomi_risiko_relevan():
    """UI checklist taksonomi Danantara (menggantikan taksonomi lama)."""
    st.subheader("Taksonomi Risiko (Danantara) 📝")
    with st.expander("**Pilih Kategori Taksonomi Risiko**", expanded=True):
        # normalisasi state
        if isinstance(st.session_state["selected_taxonomi"], str):
            try:
                st.session_state["selected_taxonomi"] = json.loads(st.session_state["selected_taxonomi"])
            except json.JSONDecodeError:
                st.session_state["selected_taxonomi"] = []

        selected = st.session_state.get("selected_taxonomi", [])
        new_selection = []

        for category, items in DANANTARA_TAXONOMY.items():
            st.markdown(f"**{category}**")
            for item in items:
                unique_key = f"chk_{category.replace(' ', '_')}_{item['kode']}"
                is_checked = any(sel.get("kode") == item["kode"] for sel in selected)
                checked = st.checkbox(f"{item['kode']} - {item['nama']}", key=unique_key, value=is_checked)
                if checked:
                    if item not in new_selection:
                        new_selection.append(item)

        # simpan
        if new_selection != selected:
            st.session_state["selected_taxonomi"] = new_selection

        if st.button("✅ Simpan Pilihan", key="update_taxonomy_selection"):
            st.success("✅ Pilihan Taksonomi Risiko berhasil diperbarui!")

        st.write("---")
        if new_selection:
            st.write("Anda telah memilih:")
            for idx, item in enumerate(new_selection, start=1):
                st.write(f"{idx}. {item['kode']} - {item['nama']}")
        else:
            st.write("Belum ada pilihan.")

        return DANANTARA_TAXONOMY

# =========================
# OpenAI (robust wrapper)
# =========================

def get_gpt_response(prompt, system_message="", model="gpt-4o-mini", temperature=0.2, max_tokens=1200):
    """Kirim prompt ke OpenAI. Batasi token agar JSON tak kepotong."""
    try:
        if not os.getenv("OPENAI_API_KEY"):
            return "❌ OPENAI_API_KEY belum diset pada environment."
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=60
        )
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Error saat menghubungi GPT: {e}"

def saran_gpt_metrix_strategi_risiko():
    st.markdown("### 🤖 Saran AI: Metrix Strategi Risiko")

    selected_taxonomies = st.session_state.get("selected_taxonomi", [])
    if not selected_taxonomies:
        st.warning("⚠️ Anda belum memilih taksonomi risiko. Pilih taksonomi terlebih dahulu.")
        return

    if st.button("🔍 Dapatkan Saran AI"):
        status = st.empty()
        raw_expander = st.expander("🔎 Lihat raw output AI (debug)", expanded=False)
        status.info("📡 Menyiapkan permintaan ke AI...")

        base_instructions = """
Anda adalah asisten ERM. BALAS HANYA dengan JSON array valid tanpa teks lain.
Jangan gunakan bullet, heading, atau catatan di luar JSON.

Format WAJIB: sebuah JSON array of objects. Contoh minimal: [{"a":1}]

Kolom wajib per item:
- "Kode Risiko"
- "Kategori Risiko T2 & T3 KBUMN"    # isi dengan nama kategori Danantara
- "Risk Appetite Statement"
- "Sikap Terhadap Risiko"            # salah satu: "Strategis", "Moderat", "Konservatif", "Tidak toleran"
- "Parameter"
- "Satuan Ukuran"
- "Nilai Batasan/Limit"

Aturan:
- Berikan satu objek untuk SETIAP kategori yang dikirim.
- Tanpa komentar/pembuka/penutup. JSON murni saja.
"""

        user_payload = f"""
Kategori yang dipilih user (Taksonomi Danantara):
{json.dumps(selected_taxonomies, indent=2, ensure_ascii=False)}

Keluarkan array JSON sesuai kolom wajib. Pastikan valid secara JSON.
"""

        def _ask_ai(temp=0.2, max_tokens=1200):
            return get_gpt_response(
                prompt=user_payload,
                system_message=base_instructions,
                model="gpt-4o-mini",
                temperature=temp,
                max_tokens=max_tokens
            )

        # ---- Try #1 ----
        status.info("🧠 Menghubungi AI (percobaan 1)...")
        ai_text = _ask_ai()
        raw_expander.code(ai_text or "", language="json")

        data = extract_json_robust(ai_text)
        if data is None:
            # ---- Try #2 (retry lebih keras) ----
            status.warning("♻️ Respons belum JSON murni. Mencoba ulang dengan instruksi lebih ketat...")
            harder = base_instructions + "\n\nPENTING: Outputkan HANYA array JSON. Jika gagal, outputkan [] tanpa teks lain."
            def _ask_ai_harder():
                return get_gpt_response(
                    prompt=user_payload,
                    system_message=harder,
                    model="gpt-4o-mini",
                    temperature=0.0,
                    max_tokens=1000
                )
            ai_text2 = _ask_ai_harder()
            raw_expander.code(ai_text2 or "", language="json")
            data = extract_json_robust(ai_text2)

        if data is None:
            st.error("⚠️ Format output AI tidak valid: tidak ditemukan JSON array. Coba ulang.")
            return

        # Validasi & normalisasi
        expected_columns = [
            "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN",
            "Risk Appetite Statement", "Sikap Terhadap Risiko",
            "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
        ]
        df_recommended = pd.DataFrame.from_records(data)

        # Tambahkan kolom yang hilang
        for c in expected_columns:
            if c not in df_recommended.columns:
                df_recommended[c] = ""

        # Normalisasi Sikap
        valid_attitudes = ["Strategis", "Moderat", "Konservatif", "Tidak toleran"]
        df_recommended["Sikap Terhadap Risiko"] = df_recommended["Sikap Terhadap Risiko"].apply(
            lambda x: x if x in valid_attitudes else "Moderat"
        )

        # Simpan ke state
        st.session_state["metrix_strategi"] = df_recommended.reset_index(drop=True).copy()
        st.session_state["copy_metrix_strategi_risiko"] = st.session_state["metrix_strategi"].copy()

        st.success("✅ Saran AI berhasil ditambahkan.")

def modul_metrix_strategi_risiko():
    # --- METRIX STRATEGI RISIKO ---
    st.subheader("Modul Metrix Strategi Risiko 📝")

    # Pastikan kolom ada
    for col in [
        "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN",
        "Risk Appetite Statement", "Sikap Terhadap Risiko",
        "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
    ]:
        if col not in st.session_state["metrix_strategi"].columns:
            st.session_state["metrix_strategi"][col] = ""

    # Tampilkan editor (tambah kolom No hanya untuk tampilan)
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
        use_container_width=True,
        hide_index=True
    )

    if st.button("🔄 Update Data", key="update_metrix_strategi"):
        # Buang kolom No sebelum simpan
        df_save = edited_metrix.copy()
        if "No" in df_save.columns:
            df_save = df_save.drop(columns=["No"])
        st.session_state["metrix_strategi"] = df_save
        st.session_state["copy_metrix_strategi_risiko"] = df_save.copy()
        # generate kode jika kosong
        st.session_state["metrix_strategi"] = generate_risk_codes(st.session_state["metrix_strategi"])
        st.success("✅ Data pada 'Metrix Strategi Risiko' diperbarui & disalin.")

# =========================
# Export ke Excel
# =========================

def save_and_download_strategi_risiko_combined():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    kode_perusahaan = st.session_state.get("kode_perusahaan", "Unknown")
    folder_path = os.path.join(tempfile.gettempdir(), "risma_exports")
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

# =========================
# Main App
# =========================

def main():
    st.title("📊 Strategi Risiko - Upload & Analisa Data")
    initialize_data()

    # --- Upload file Excel (Profil Perusahaan & Strategi Risiko) ---
    uploaded_file = st.file_uploader("📥 Pilih file Excel (.xlsx)", type=["xlsx"], key="data_uploader")

    # --- Proses file ter-upload ---
    if uploaded_file is not None:
        try:
            file_name = uploaded_file.name.lower()
            ext = os.path.splitext(file_name)[1]

            if ext != ".xlsx":
                st.error("❌ Format .xls tidak didukung. Simpan sebagai .xlsx.")
                return

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

            # Proses Profil Perusahaan
            if profil_sheets:
                profil_data = {}
                for sheet in profil_sheets:
                    df = xls.parse(sheet)
                    sheet_key = sheet.lower().replace(" ", "_")
                    profil_data[sheet_key] = df.copy()

                st.session_state["copy2_profil_perusahaan"] = profil_data
                st.success(f"✅ Data Profil Perusahaan berhasil dimuat ({len(profil_data)} tabel).")

            # Proses Strategi Risiko
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

    # --- Load Data Profil Perusahaan dari Session ---
    profil_perusahaan = st.session_state.get("copy2_profil_perusahaan", {})
    informasi_perusahaan_df = profil_perusahaan.get("informasi_perusahaan", pd.DataFrame())

    # --- Tampilkan Profil Perusahaan ---
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
                    total_aset_dari_profil = _to_int(total_aset_value)
            except Exception as e:
                st.warning(f"⚠️ Ada masalah membaca data profil perusahaan: {e}")

            for _, row in informasi_perusahaan_df.iterrows():
                kolom_data = str(row.get("Data yang dibutuhkan", "")).strip()
                kolom_input = str(row.get("Input Pengguna", "")).strip()
                st.markdown(f"**{kolom_data}**: {kolom_input}")
        else:
            st.warning("⚠️ Profil perusahaan belum dimuat atau kosong.")

    # --- Input Total Aset ---
    st.subheader("💰 Input Total Aset")
    if total_aset_dari_profil is not None:
        total_aset_input = st.text_input("Total Aset (diambil dari Profil Perusahaan):", value=f"{total_aset_dari_profil:,}")
    else:
        total_aset_input = st.text_input("Total Aset:", value="", placeholder="Contoh: 13.000.000.000.000")

    total_aset = _to_int(total_aset_input)

    # --- Ambang Batas Risiko (Editor) ---
    st.write("### 📊 Ambang Batas Risiko")

    df_ambang = pd.DataFrame(st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame()))
    if df_ambang.empty:
        df_ambang = st.session_state["ambang_batas"].copy()

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

                # Update limit risiko juga
                baris_limit = df_ambang[df_ambang["Ambang Batas"] == "Limit Risiko"]
                if not baris_limit.empty:
                    nilai_limit = baris_limit["Nilai"].values[0]
                    parsed = _to_int(nilai_limit)
                    st.session_state["copy_limit_risiko"] = parsed if parsed is not None else nilai_limit

                st.success("✅ Data Ambang Batas Risiko berhasil diperbarui.")
            else:
                st.warning("⚠️ Belum ada data untuk disalin.")

    with col2:
        if st.button("📊 Hitung Ambang Batas"):
            if not total_aset:
                st.error("❌ Total Aset tidak valid. Mohon masukkan angka yang benar.")
            else:
                st.write(f"🔎 Total Aset digunakan untuk perhitungan: `{total_aset:,}`")
                hasil_perhitungan, limit_risk = modul_ambang_batas(total_aset)
                if hasil_perhitungan is not None and limit_risk is not None:
                    try:
                        # Ambil editan user dari editor bila ada dan merge
                        df_edit = st.session_state.get("editor_ambang_batas")
                        if df_edit is not None and "Ambang Batas" in df_edit.columns:
                            for idx, row in hasil_perhitungan.iterrows():
                                ambang = row["Ambang Batas"]
                                if ambang in df_edit["Ambang Batas"].values:
                                    nilai_edit = df_edit.loc[df_edit["Ambang Batas"] == ambang, "Nilai"].values[0]
                                    hasil_perhitungan.at[idx, "Nilai"] = nilai_edit
                    except Exception:
                        st.warning("⚠️ Tekan '📋 Update Data' bila perubahan belum terlihat.")

                    st.session_state["copy_ambang_batas_risiko"] = hasil_perhitungan.copy()
                    st.session_state["copy_limit_risiko"] = limit_risk
                    st.success("✅ Ambang Batas berhasil dihitung & digabung dengan editan pengguna.")
                else:
                    st.warning("⚠️ Perhitungan gagal. Total aset tidak valid atau nol.")

    # --- Tabel Final ---
    st.markdown("### 📌 Tabel Ambang Batas Risiko (Final)")
    df_final = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame()).copy()
    if isinstance(df_final, pd.DataFrame) and not df_final.empty:
        df_final = df_final.reset_index(drop=True)
        st.dataframe(df_final, hide_index=True)
    else:
        st.info("📭 Belum ada data ambang batas risiko. Isi manual atau klik **Hitung Ambang Batas**.")

    if st.button("📋 Simpan Ulang dari Tabel Final"):
        if not edited_ambang_batas.empty:
            df_ambang.loc[:, "Nilai"] = edited_ambang_batas["Nilai"]
            st.session_state["copy_ambang_batas_risiko"] = df_ambang.drop(columns=["No"]).copy()

            baris_limit = df_ambang[df_ambang["Ambang Batas"] == "Limit Risiko"]
            if not baris_limit.empty:
                nilai_limit = baris_limit["Nilai"].values[0]
                parsed = _to_int(nilai_limit)
                st.session_state["copy_limit_risiko"] = parsed if parsed is not None else nilai_limit

            st.success("✅ Data Ambang Batas Risiko berhasil diperbarui.")
        else:
            st.warning("⚠️ Belum ada data untuk disalin.")

    # --- Modul Lanjutan ---
    tampilkan_taksonomi_risiko_relevan()
    saran_gpt_metrix_strategi_risiko()
    modul_metrix_strategi_risiko()

    # --- Export ---
    save_and_download_strategi_risiko_combined()

# Entrypoint
if __name__ == "__main__":
    main()
