# modules/strategi_risiko.py
# ======================================================
# Strategi Risiko — Upload, Ambang Batas, Taksonomi (Checkbox),
# AI Penyebab Utama → Pilih Penyebab → AI Metrix, Editor, Export
# ======================================================

import streamlit as st
import pandas as pd
import os
import re
import openai
import json
import io
from datetime import datetime

# ====== Taksonomi Risiko (BARU, sesuai instruksi) ======
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

# ======================================================
# Utils
# ======================================================

def extract_json(response_text: str):
    """Ambil JSON array valid dari teks (jawaban model)."""
    try:
        m = re.search(r"\[.*\]", response_text or "", flags=re.DOTALL)
        if not m:
            return None
        return json.loads(m.group())
    except Exception:
        return None

def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(s)).strip("_").lower()

def generate_risk_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Autogenerate 'Kode Risiko' jika kosong, berdasarkan kolom kategori."""
    if "Kode Risiko" not in df.columns:
        df["Kode Risiko"] = ""
    for i, row in df.iterrows():
        if not str(row.get("Kode Risiko", "")).strip():
            kategori = str(row.get("Kategori Risiko T2 & T3 KBUMN", "GEN"))
            prefix = re.sub(r"[^A-Za-z]", "", kategori[:3]).upper() or "GEN"
            df.at[i, "Kode Risiko"] = f"RISK-{prefix}-{i+1}"
    return df

# ======================================================
# Ambang Batas
# ======================================================

def modul_ambang_batas(total_aset: int):
    """Hitung ambang batas risiko (capacity, appetite, tolerance, limit)."""
    if total_aset is None or total_aset <= 0:
        return None, None

    risk_capacity = int(total_aset * 0.15)
    risk_appetite = int(0.3 * risk_capacity)
    risk_tolerance = int(0.4 * risk_capacity)
    limit_risk = int(0.2 * risk_capacity)

    hasil = pd.DataFrame({
        "Ambang Batas": [
            "Total Aset", "Risk Capacity", "Risk Appetite", "Risk Tolerance", "Limit Risiko"
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
    return hasil, limit_risk

# ======================================================
# Metrix (Editor)
# ======================================================

def modul_metrix_strategi_risiko():
    st.subheader("📝 Metrix Strategi Risiko (Editor Manual)")
    if "metrix_strategi" not in st.session_state:
        st.session_state["metrix_strategi"] = pd.DataFrame(columns=[
            "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN", "Risk Appetite Statement",
            "Sikap Terhadap Risiko", "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
        ])

    df_display = st.session_state["metrix_strategi"].copy()
    if "Kode Risiko" not in df_display.columns:
        df_display["Kode Risiko"] = ""
    df_display.insert(0, "No", range(1, len(df_display)+1))

    edited = st.data_editor(
        df_display,
        key="metrix_strategi_editor",
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("🔄 Update Data", key="btn_update_metrix"):
        df_updated = edited.copy()
        if "No" in df_updated.columns:
            df_updated = df_updated.drop(columns=["No"])
        df_updated = generate_risk_codes(df_updated)
        st.session_state["metrix_strategi"] = df_updated.copy()
        st.session_state["copy_metrix_strategi_risiko"] = df_updated.copy()
        st.success("✅ Metrix diperbarui & disalin.")

# ======================================================
# Taksonomi (Checkbox)
# ======================================================

def tampilkan_taksonomi_risiko_relevan():
    st.subheader("🧭 Taksonomi Risiko (Checkbox)")
    with st.expander("Pilih item risiko yang relevan per kategori", expanded=True):

        if "selected_taxonomi" not in st.session_state:
            # list of dict: {"kategori": "...", "risiko": "..."}
            st.session_state["selected_taxonomi"] = []

        current = st.session_state["selected_taxonomi"]
        selected_set = {(d["kategori"], d["risiko"]) for d in current if isinstance(d, dict)}
        new_selection = set(selected_set)

        for category, items in TAXONOMY.items():
            cat_slug = _slug(category)
            st.markdown(f"### {category}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✔️ Pilih semua", key=f"btn_all_{cat_slug}"):
                    for r in items:
                        new_selection.add((category, r))
            with c2:
                if st.button("🧹 Kosongkan", key=f"btn_none_{cat_slug}"):
                    for r in items:
                        new_selection.discard((category, r))

            for r in items:
                item_slug = _slug(r)
                key = f"chk_{cat_slug}_{item_slug}"
                checked_default = (category, r) in new_selection
                checked = st.checkbox(r, value=checked_default, key=key)
                if checked:
                    new_selection.add((category, r))
                else:
                    new_selection.discard((category, r))

            st.write("---")

        st.session_state["selected_taxonomi"] = [
            {"kategori": c, "risiko": r} for (c, r) in sorted(new_selection)
        ]

        if st.button("✅ Simpan Pilihan", key="btn_save_taxo"):
            st.success("✅ Pilihan Taksonomi Risiko tersimpan.")

        chosen = st.session_state["selected_taxonomi"]
        if chosen:
            st.markdown("**Ringkasan Pilihan:**")
            for i, d in enumerate(chosen, start=1):
                st.write(f"{i}. {d['kategori']} — {d['risiko']}")
        else:
            st.info("Belum ada pilihan.")

        return TAXONOMY

# ======================================================
# AI Helpers
# ======================================================

def get_gpt_response(prompt, system_message="", model="gpt-4", temperature=0.4, max_tokens=3000):
    """Wrapper OpenAI ChatCompletion (pastikan OPENAI_API_KEY ada di env)."""
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Error saat menghubungi GPT: {e}"

# ======================================================
# (BARU) AI: REKOMENDASI PENYEBAB UTAMA → PILIH PENYEBAB
# ======================================================

def ai_rekomendasi_penyebab_utama():
    """
    Menghasilkan 3 rekomendasi penyebab utama untuk setiap risiko yang dipilih.
    Simpan di st.session_state["root_cause_options"] sebagai dict:
      { "<kategori>|<risiko>": ["causal-1","causal-2","causal-3"], ... }
    """
    st.subheader("🧠 AI: Rekomendasi Penyebab Utama")
    selected = st.session_state.get("selected_taxonomi", [])
    if not selected:
        st.warning("⚠️ Belum ada taksonomi yang dipilih.")
        return

    if "root_cause_options" not in st.session_state:
        st.session_state["root_cause_options"] = {}

    if st.button("🔍 Dapatkan 3 Penyebab Utama per Risiko", key="btn_get_causes"):
        progress = st.progress(0, text="📡 Menyiapkan permintaan...")
        try:
            progress.progress(20, "📄 Menyusun prompt...")

            # Siapkan payload sederhana
            payload = {
                "risks_selected": selected,  # [{"kategori": "...", "risiko": "..."}]
                "expected_format": [
                    {
                        "kategori": "🖥️ Operational Risk",
                        "risiko": "Cyber Attack Sistem Informasi",
                        "penyebab_utama": ["..", "..", ".."]
                    }
                ]
            }

            prompt = f"""
Berikut daftar risiko yang dipilih user (JSON):
{json.dumps(payload, indent=2, ensure_ascii=False)}

TUGAS:
- Untuk SETIAP objek risiko di atas, kembalikan persis format:
  {{
    "kategori": "...",
    "risiko": "...",
    "penyebab_utama": ["Penyebab-1", "Penyebab-2", "Penyebab-3"]
  }}
- Hanya balas dengan JSON array valid (tanpa teks lain).
- Penyebab harus spesifik, actionable, dan menjelaskan sumber akar (people/process/technology/external).
"""

            progress.progress(45, "🧠 Menghubungi GPT...")
            ai_text = get_gpt_response(
                prompt,
                system_message="Anda asisten AI untuk analisis risiko perusahaan pelabuhan.",
                temperature=0.3,
                max_tokens=3000
            )

            progress.progress(65, "📥 Parsing respons AI...")
            data = extract_json(ai_text)
            if not data:
                raise ValueError("Respons AI tidak mengandung JSON valid.")

            # Simpan ke state
            options = {}
            for row in data:
                kategori = row.get("kategori")
                risiko = row.get("risiko")
                causes = row.get("penyebab_utama", [])
                if kategori and risiko and isinstance(causes, list):
                    key = f"{kategori}|{risiko}"
                    options[key] = causes[:3]  # ambil maksimal 3

            st.session_state["root_cause_options"] = options
            progress.progress(100, "✅ Penyebab utama berhasil diambil.")
            st.success("✅ Rekomendasi 3 penyebab utama per risiko sudah tersedia.")
        except Exception as e:
            st.error(f"❌ Gagal mengambil rekomendasi penyebab: {e}")

def ui_pilih_penyebab_utama():
    """
    Tampilkan UI pilihan penyebab utama per risiko.
    Simpan pilihan user di st.session_state["root_cause_selected"]:
      { "<kategori>|<risiko>": "<selected_cause>" }
    """
    st.subheader("🧩 Pilih Penyebab Utama per Risiko")
    options = st.session_state.get("root_cause_options", {})
    selected = st.session_state.get("selected_taxonomi", [])

    if not selected:
        st.info("Belum ada risiko yang dipilih.")
        return

    if not options:
        st.info("Belum ada rekomendasi penyebab. Tekan tombol 'Dapatkan 3 Penyebab Utama per Risiko' di atas.")
        return

    if "root_cause_selected" not in st.session_state:
        st.session_state["root_cause_selected"] = {}

    for item in selected:
        kategori, risiko = item["kategori"], item["risiko"]
        key = f"{kategori}|{risiko}"
        daftar = options.get(key, [])
        st.markdown(f"**{kategori} — {risiko}**")

        if daftar:
            # radio satu pilihan (bisa diubah ke selectbox/multiselect bila perlu)
            default_idx = 0
            if key in st.session_state["root_cause_selected"]:
                try:
                    default_idx = daftar.index(st.session_state["root_cause_selected"][key])
                except ValueError:
                    default_idx = 0
            choice = st.radio(
                "Pilih penyebab utama:",
                daftar,
                index=default_idx if default_idx < len(daftar) else 0,
                key=_slug(f"rc_{key}")
            )
            st.session_state["root_cause_selected"][key] = choice
        else:
            st.warning("AI belum memberikan opsi penyebab untuk item ini.")

        st.write("---")

# ======================================================
# (DISESUAIKAN) AI: Saran Metrix berdasarkan Penyebab Utama terpilih
# ======================================================

def saran_gpt_metrix_strategi_risiko():
    st.markdown("### 🤖 Saran AI: Metrix Strategi Risiko (berdasarkan penyebab utama)")

    selected_taxonomies = st.session_state.get("selected_taxonomi", [])
    if not selected_taxonomies:
        st.warning("⚠️ Belum ada pilihan taksonomi.")
        return

    selected_causes = st.session_state.get("root_cause_selected", {})
    if not selected_causes:
        st.warning("⚠️ Belum ada penyebab utama yang dipilih.")
        return

    # Bangun payload terstruktur untuk GPT
    rows = []
    for item in selected_taxonomies:
        kategori, risiko = item["kategori"], item["risiko"]
        key = f"{kategori}|{risiko}"
        cause = selected_causes.get(key)
        rows.append({
            "kategori": kategori,
            "risiko": risiko,
            "penyebab_utama_terpilih": cause
        })

    if st.button("🧮 Bangun Metrix Risiko (AI)", key="btn_call_ai_metrix"):
        progress = st.progress(0, text="📡 Menyiapkan permintaan...")
        try:
            progress.progress(25, "📄 Menyusun prompt...")

            payload = {
                "risks_with_root_cause": rows,
                "expected_columns": [
                    "Kode Risiko",
                    "Kategori Risiko T2 & T3 KBUMN",
                    "Risk Appetite Statement",
                    "Sikap Terhadap Risiko",
                    "Parameter",
                    "Satuan Ukuran",
                    "Nilai Batasan/Limit"
                ],
                "guidance": [
                    "Gunakan 'kategori' langsung untuk kolom 'Kategori Risiko T2 & T3 KBUMN'.",
                    "Turunkan Parameter, Satuan Ukuran, dan Nilai Limit dari 'penyebab_utama_terpilih' agar actionable.",
                    "Risk Appetite Statement harus jelas & dapat diukur.",
                    "Sikap Terhadap Risiko salah satu dari: Strategis, Moderat, Konservatif, Tidak toleran."
                ]
            }

            prompt = f"""
Berikut daftar risiko dan penyebab utama terpilih (JSON):
{json.dumps(payload, indent=2, ensure_ascii=False)}

TUGAS:
- Hasilkan satu baris untuk SETIAP entri pada 'risks_with_root_cause'.
- Balas HANYA dalam bentuk JSON array valid, tanpa teks lain.
- Kolom persis:
  - "Kode Risiko" (boleh kosong)
  - "Kategori Risiko T2 & T3 KBUMN" (ISI DENGAN NILAI 'kategori')
  - "Risk Appetite Statement"
  - "Sikap Terhadap Risiko" (Strategis|Moderat|Konservatif|Tidak toleran)
  - "Parameter"
  - "Satuan Ukuran"
  - "Nilai Batasan/Limit"
- Pastikan Parameter, Satuan Ukuran, dan Nilai Limit konsisten dengan penyebab utama terpilih.
- JSON wajib valid.
"""

            progress.progress(55, "🧠 Menghubungi GPT...")
            ai_text = get_gpt_response(
                prompt,
                system_message="Anda asisten AI untuk analisis risiko perusahaan pelabuhan. Jawaban harus JSON valid.",
                temperature=0.35,
                max_tokens=4000
            )

            progress.progress(75, "📥 Parsing respons AI...")
            data = extract_json(ai_text)
            if not data:
                raise ValueError("Respons AI tidak mengandung JSON valid.")

            expected_cols = [
                "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN",
                "Risk Appetite Statement", "Sikap Terhadap Risiko",
                "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
            ]
            df = pd.DataFrame.from_records(data)
            miss = [c for c in expected_cols if c not in df.columns]
            if miss:
                raise ValueError(f"Kolom hilang: {miss}")

            # Normalisasi nilai sikap
            valid_att = ["Strategis", "Moderat", "Konservatif", "Tidak toleran"]
            df["Sikap Terhadap Risiko"] = df["Sikap Terhadap Risiko"].apply(
                lambda x: x if x in valid_att else "Moderat"
            )

            df = df.reset_index(drop=True)
            df = generate_risk_codes(df)

            st.session_state["metrix_strategi"] = df.copy()
            st.session_state["temp_metrix_strategi_risiko"] = df.copy()
            st.session_state["copy_metrix_strategi_risiko"] = df.copy()

            progress.progress(100, "✅ Selesai!")
            st.success("✅ Metrix Risiko berbasis penyebab utama berhasil dibuat.")
        except Exception as e:
            st.error(f"❌ Gagal membangun Metrix: {e}")

# ======================================================
# Save / Download (Excel)
# ======================================================

def save_and_download_strategi_risiko_combined():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    kode_perusahaan = st.session_state.get("kode_perusahaan", "Unknown")

    # Folder server (opsional)
    folder_path = "C:/saved"
    try:
        os.makedirs(folder_path, exist_ok=True)
    except Exception:
        folder_path = None

    nama_file = f"Strategi_Risiko_{kode_perusahaan}_{timestamp}.xlsx"
    server_file_path = os.path.join(folder_path, nama_file) if folder_path else None

    df_copy_ambang = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame())
    limit_value = st.session_state.get("copy_limit_risiko", "-")
    df_limit = pd.DataFrame([{"Limit Risiko": limit_value}])
    df_metrix_copy = st.session_state.get("copy_metrix_strategi_risiko", pd.DataFrame())

    output = io.BytesIO()
    try:
        if server_file_path:
            with pd.ExcelWriter(server_file_path, engine="xlsxwriter") as w:
                df_copy_ambang.to_excel(w, sheet_name="Copy Ambang Batas Risiko", index=False)
                df_limit.to_excel(w, sheet_name="Copy Limit Risiko", index=False)
                df_metrix_copy.to_excel(w, sheet_name="Copy Metrix Strategi Risiko", index=False)

        with pd.ExcelWriter(output, engine="xlsxwriter") as w2:
            df_copy_ambang.to_excel(w2, sheet_name="Copy Ambang Batas Risiko", index=False)
            df_limit.to_excel(w2, sheet_name="Copy Limit Risiko", index=False)
            df_metrix_copy.to_excel(w2, sheet_name="Copy Metrix Strategi Risiko", index=False)

        output.seek(0)
        if server_file_path:
            st.success(f"✅ File tersimpan di server: `{server_file_path}`")

        st.download_button(
            label="⬇️ Unduh Strategi Risiko (Excel)",
            data=output,
            file_name=nama_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"❌ Gagal menyimpan/menyiapkan unduhan: {e}")

# ======================================================
# MAIN
# ======================================================

def main():
    st.title("📊 Strategi Risiko — Upload & Analisis")

    # Upload file Excel (opsional)
    uploaded_file = st.file_uploader("📥 Unggah file Excel (opsional)", type=["xls", "xlsx"], key="uploader")
    st.session_state.setdefault("kode_perusahaan", "Unknown")
    st.session_state.setdefault("copy_ambang_batas_risiko", pd.DataFrame())
    st.session_state.setdefault("copy_limit_risiko", "-")
    st.session_state.setdefault("copy_metrix_strategi_risiko", pd.DataFrame())
    st.session_state.setdefault("metrix_strategi", pd.DataFrame(columns=[
        "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN", "Risk Appetite Statement",
        "Sikap Terhadap Risiko", "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
    ]))

    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file, engine="openpyxl")
            sheet_names = [s.strip() for s in xls.sheet_names]

            expected_strategi = [
                "Copy Ambang Batas Risiko",
                "Copy Limit Risiko",
                "Copy Metrix Strategi Risiko"
            ]

            profil_sheets, strategi_sheets = [], []
            for s in sheet_names:
                (strategi_sheets if s in expected_strategi else profil_sheets).append(s)

            if profil_sheets:
                profil_data = {}
                for s in profil_sheets:
                    df = xls.parse(s)
                    profil_data[s.lower().replace(" ", "_")] = df.copy()
                st.session_state["copy2_profil_perusahaan"] = profil_data
                st.success(f"✅ Profil Perusahaan dimuat ({len(profil_data)} sheet).")

            if "Copy Ambang Batas Risiko" in strategi_sheets:
                st.session_state["copy_ambang_batas_risiko"] = xls.parse("Copy Ambang Batas Risiko")

            if "Copy Limit Risiko" in strategi_sheets:
                df_limit = xls.parse("Copy Limit Risiko")
                if not df_limit.empty and "Limit Risiko" in df_limit.columns:
                    st.session_state["copy_limit_risiko"] = df_limit["Limit Risiko"].iloc[0]
                else:
                    st.warning("⚠️ Sheet 'Copy Limit Risiko' ada, tapi kolom tidak sesuai.")

            if "Copy Metrix Strategi Risiko" in strategi_sheets:
                df_metrix = xls.parse("Copy Metrix Strategi Risiko")
                st.session_state["copy_metrix_strategi_risiko"] = df_metrix.copy()
                st.session_state["metrix_strategi"] = df_metrix.copy()

            if strategi_sheets:
                st.success(f"✅ Strategi Risiko dimuat ({len(strategi_sheets)} sheet).")

            unknown = [s for s in sheet_names if s not in (profil_sheets + strategi_sheets)]
            if unknown:
                st.warning(f"⚠️ Sheet tidak dikenali: {', '.join(unknown)}")

        except Exception as e:
            st.error(f"❌ Gagal memuat Excel: {e}")

    # Profil Perusahaan (opsional)
    profil_perusahaan = st.session_state.get("copy2_profil_perusahaan", {})
    informasi_df = profil_perusahaan.get("informasi_perusahaan", pd.DataFrame())
    total_aset_dari_profil = None

    with st.expander("🏢 Profil Perusahaan (opsional)", expanded=False):
        if not informasi_df.empty:
            try:
                kode_row = informasi_df[informasi_df["Data yang dibutuhkan"].str.contains("Kode Perusahaan", case=False, na=False)]
            except Exception:
                kode_row = pd.DataFrame()

            try:
                aset_row = informasi_df[informasi_df["Data yang dibutuhkan"].str.contains("Total Aset", case=False, na=False)]
            except Exception:
                aset_row = pd.DataFrame()

            if not kode_row.empty:
                st.session_state["kode_perusahaan"] = str(kode_row.iloc[0].get("Input Pengguna", "Unknown"))

            if not aset_row.empty:
                raw = str(aset_row.iloc[0].get("Input Pengguna", ""))
                if str(raw).replace(".", "").replace(",", "").isdigit():
                    total_aset_dari_profil = int(str(raw).replace(".", "").replace(",", ""))

            st.dataframe(informasi_df, use_container_width=True, hide_index=True)
        else:
            st.caption("Belum ada profil yang diunggah — opsional.")

    # Input Total Aset & Ambang Batas
    st.subheader("💰 Total Aset & Ambang Batas")
    if total_aset_dari_profil is not None:
        total_aset_input = st.text_input("Total Aset (dari Profil):", value=str(total_aset_dari_profil))
    else:
        total_aset_input = st.text_input("Total Aset:", value="", placeholder="Contoh: 13000000000000")

    try:
        total_aset_val = int(str(total_aset_input).replace(".", "").replace(",", ""))
    except Exception:
        total_aset_val = None

    # Tabel Ambang Batas (editable)
    st.markdown("### 📊 Ambang Batas Risiko")
    df_ambang = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame()).copy()
    if df_ambang.empty:
        df_ambang = pd.DataFrame({
            "Ambang Batas": ["Total Aset", "Risk Capacity", "Risk Appetite", "Risk Tolerance", "Limit Risiko"],
            "Nilai": ["-", "-", "-", "-", "-"]
        })
    df_ambang = df_ambang.reset_index(drop=True)
    df_ambang.insert(0, "No", range(1, len(df_ambang)+1))

    edited_ambang = st.data_editor(
        df_ambang[["Ambang Batas", "Nilai"]],
        key="editor_ambang_batas",
        num_rows="fixed",
        hide_index=True
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📋 Update Data Ambang Batas"):
            if not edited_ambang.empty:
                df_ambang.loc[:, "Nilai"] = edited_ambang["Nilai"]
                st.session_state["copy_ambang_batas_risiko"] = df_ambang.drop(columns=["No"]).copy()
                # refresh limit
                try:
                    val = st.session_state["copy_ambang_batas_risiko"].loc[
                        st.session_state["copy_ambang_batas_risiko"]["Ambang Batas"]=="Limit Risiko", "Nilai"
                    ].iloc[0]
                    st.session_state["copy_limit_risiko"] = int(str(val).replace(".", "").replace(",", ""))
                except Exception:
                    st.session_state["copy_limit_risiko"] = "-"
                st.success("✅ Ambang Batas diperbarui.")
            else:
                st.warning("⚠️ Tidak ada data untuk disalin.")

    with c2:
        if st.button("📊 Hitung Ambang Batas Otomatis"):
            if total_aset_val and total_aset_val > 0:
                hasil, limit_risk = modul_ambang_batas(total_aset_val)
                if hasil is not None:
                    # merge dengan edit terakhir jika ada
                    try:
                        df_edit_state = st.session_state["editor_ambang_batas"]
                        if "Ambang Batas" in df_edit_state.columns and "Nilai" in df_edit_state.columns:
                            for i, row in hasil.iterrows():
                                amb = row["Ambang Batas"]
                                if amb in list(df_edit_state["Ambang Batas"].values):
                                    hasil.at[i, "Nilai"] = df_edit_state.loc[
                                        df_edit_state["Ambang Batas"] == amb, "Nilai"
                                    ].values[0]
                    except Exception:
                        pass

                    st.session_state["copy_ambang_batas_risiko"] = hasil.copy()
                    st.session_state["copy_limit_risiko"] = limit_risk
                    st.success("✅ Ambang Batas dihitung & diperbarui.")
            else:
                st.error("❌ Total Aset tidak valid.")

    st.markdown("### 📌 Tabel Ambang Batas (Final)")
    df_final = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame()).copy()
    if not df_final.empty:
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data final.")

    if st.button("📋 Simpan Ulang dari Tabel Final"):
        if not edited_ambang.empty:
            df_ambang.loc[:, "Nilai"] = edited_ambang["Nilai"]
            st.session_state["copy_ambang_batas_risiko"] = df_ambang.drop(columns=["No"]).copy()
            try:
                val = st.session_state["copy_ambang_batas_risiko"].loc[
                    st.session_state["copy_ambang_batas_risiko"]["Ambang Batas"]=="Limit Risiko", "Nilai"
                ].iloc[0]
                st.session_state["copy_limit_risiko"] = int(str(val).replace(".", "").replace(",", ""))
            except Exception:
                st.session_state["copy_limit_risiko"] = "-"
            st.success("✅ Disalin ulang dari tabel final.")
        else:
            st.warning("⚠️ Tidak ada data untuk disalin.")

    # === 1) Taksonomi (Checkbox) ===
    tampilkan_taksonomi_risiko_relevan()

    # === 2) AI Rekomendasi Penyebab Utama ===
    ai_rekomendasi_penyebab_utama()

    # === 3) Pilih Penyebab Utama ===
    ui_pilih_penyebab_utama()

    # === 4) AI Metrix berbasis Penyebab Utama ===
    saran_gpt_metrix_strategi_risiko()

    # === 5) Editor Metrix Manual (opsional revisi) ===
    modul_metrix_strategi_risiko()

    # === 6) Export Excel ===
    save_and_download_strategi_risiko_combined()

# Debugging lokal
if __name__ == "__main__":
    main()
