import streamlit as st
import pandas as pd
import os
import re
import json
import io
import uuid
from datetime import datetime
from modules.utils import get_user_file
# Optional: jika pakai OpenAI, pastikan paket & API key sudah diset di env
try:
    import openai  # type: ignore
    OPENAI_OK = True
except Exception:
    OPENAI_OK = False


# =========================
# Util: Parser & Helpers
# =========================

def parse_int_like(x: str | int | float | None) -> int | None:
    """Parse angka dengan toleransi titik/koma/spasi. Return None jika gagal."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        try:
            return int(x)
        except Exception:
            return None
    s = str(x)
    # buang semua char non-digit
    s = re.sub(r"[^\d-]", "", s)
    if s in ("", "-", "--"):
        return None
    try:
        return int(s)
    except Exception:
        return None


def extract_json(response_text: str):
    """
    Ambil blok JSON array pertama dengan regex non-greedy.
    Return list/dict hasil json.loads atau None jika gagal.
    """
    try:
        # cari array JSON paling awal, non-greedy
        m = re.search(r"\[\s*{.*?}\s*\]", response_text, flags=re.DOTALL)
        if not m:
            return None
        return json.loads(m.group(0))
    except Exception:
        return None


# =========================
# Inisialisasi State
# =========================

def init_state():
    st.session_state.setdefault(
        "ambang_batas",
        pd.DataFrame(columns=["Ambang Batas", "Nilai"])
    )
    st.session_state.setdefault(
        "copy_ambang_batas_risiko",
        pd.DataFrame(columns=["Ambang Batas", "Nilai"])
    )
    st.session_state.setdefault("copy_limit_risiko", "-")
    st.session_state.setdefault(
        "metrix_strategi",
        pd.DataFrame(columns=[
            "Kode Risiko",
            "Kategori Risiko T2 & T3 KBUMN",
            "Risk Appetite Statement",
            "Sikap Terhadap Risiko",
            "Parameter",
            "Satuan Ukuran",
            "Nilai Batasan/Limit",
        ])
    )
    st.session_state.setdefault(
        "copy_metrix_strategi_risiko",
        pd.DataFrame(columns=[
            "Kode Risiko",
            "Kategori Risiko T2 & T3 KBUMN",
            "Risk Appetite Statement",
            "Sikap Terhadap Risiko",
            "Parameter",
            "Satuan Ukuran",
            "Nilai Batasan/Limit",
        ])
    )
    st.session_state.setdefault("kode_perusahaan", "Unknown")
    st.session_state.setdefault("selected_taxonomi", [])


# =========================
# Ambang Batas (Calculator)
# =========================

def modul_ambang_batas(total_aset: int | None):
    if not total_aset or total_aset <= 0:
        return None, None
    risk_capacity = int(total_aset * 0.15)
    risk_appetite = int(0.3 * risk_capacity)
    risk_tolerance = int(0.4 * risk_capacity)
    limit_risk = int(0.2 * risk_capacity)

    hasil = pd.DataFrame({
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
            "20% dari Risk Capacity",
        ],
    })
    return hasil, limit_risk


# =========================
# Kode Risiko Generator
# =========================

def generate_risk_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate kode risiko stabil per kategori.
    Jika sudah ada 'Kode Risiko' non-empty, dipertahankan.
    """
    df = df.copy()
    if "Kode Risiko" not in df.columns:
        df["Kode Risiko"] = ""

    # counter per kategori
    counters = {}
    for i, row in df.iterrows():
        if str(row.get("Kode Risiko", "")).strip():
            continue
        kategori = str(row.get("Kategori Risiko T2 & T3 KBUMN", "GEN")).strip() or "GEN"
        prefix = f"RISK-{kategori[:3].upper()}"
        counters.setdefault(prefix, 0)
        counters[prefix] += 1
        df.at[i, "Kode Risiko"] = f"{prefix}-{counters[prefix]:03d}"
    return df


# =========================
# UI: Taksonomi KBUMN Relevan
# =========================

def tampilkan_taksonomi_risiko_relevan():
    st.subheader("Taksonomi Risiko 📝")
    with st.expander("**Taksonomi Risiko Relevan**", expanded=True):
        st.write("Pilih Taksonomi Risiko Relevan:")

        taxonomy = {
            "1.1 Kategori Risiko Fiskal": [
                {"kode": "1.1.1", "nama": "Peristiwa Risiko terkait Dividen"},
                {"kode": "1.1.2", "nama": "Peristiwa Risiko terkait PMN"},
                {"kode": "1.1.3", "nama": "Peristiwa Risiko terkait Subsidi & Kompensasi"},
            ],
            "1.2 Kategori Risiko Kebijakan": [
                {"kode": "1.2.4", "nama": "Peristiwa Risiko terkait Kebijakan SDM"},
                {"kode": "1.2.5", "nama": "Peristiwa Risiko terkait Kebijakan Sektoral"},
            ],
            "1.3 Kategori Risiko Komposisi": [
                {"kode": "1.3.6", "nama": "Peristiwa Risiko terkait Konsentrasi Portofolio"},
            ],
            "2.4 Kategori Risiko Struktur": [
                {"kode": "2.4.7", "nama": "Peristiwa Risiko terkait Struktur Korporasi"},
            ],
            "2.5 Kategori Risiko Restrukturisasi dan Reorganisasi": [
                {"kode": "2.5.8", "nama": "Peristiwa Risiko terkait M&A, JV, Restrukturisasi"},
            ],
            "3.6 Kategori Risiko Industri Umum": [
                {"kode": "3.6.9", "nama": "Peristiwa Risiko terkait Formulasi Strategis"},
                {"kode": "3.6.10", "nama": "Peristiwa Risiko terkait Pasar & Makroekonomi (Observasi 6)"},
                {"kode": "3.6.11", "nama": "Peristiwa Risiko terkait Hukum, Reputasi & Kepatuhan (Observasi 15)"},
                {"kode": "3.6.12", "nama": "Peristiwa Risiko terkait Keuangan"},
                {"kode": "3.6.13", "nama": "Peristiwa Risiko terkait Proyek (Observasi 8)"},
                {"kode": "3.6.14", "nama": "Peristiwa Risiko terkait TI & Keamanan Siber (Observasi 12)"},
                {"kode": "3.6.15", "nama": "Peristiwa Risiko terkait Sosial & Lingkungan"},
                {"kode": "3.6.16", "nama": "Peristiwa Risiko terkait Operasional (Observasi 2-5, 13,16, 17)"},
            ],
            "3.7 Kategori Risiko Industri Perbankan": [],
            "3.8 Kategori Risiko Industri Asuransi": [],
        }

        selected = st.session_state.get("selected_taxonomi", [])
        # Rebuild pilihan (hindari state phantom)
        new_selection = []

        for category, items in taxonomy.items():
            st.markdown(f"**{category}**")
            for item in items:
                key = f"chk_{category}_{item['kode']}"
                # checked jika sudah ada di pilihan sebelumnya
                is_checked = any(sel.get("kode") == item["kode"] for sel in selected)
                checked = st.checkbox(f"{item['kode']} - {item['nama']}", key=key, value=is_checked)
                if checked:
                    new_selection.append(item)

        # update state jika berubah
        if new_selection != selected:
            st.session_state["selected_taxonomi"] = new_selection

        if st.button("✅ Simpan Pilihan", key="update_taxonomy_selection"):
            st.success("✅ Pilihan Taksonomi Risiko berhasil diperbarui!")

        st.write("---")
        if new_selection:
            st.write("Anda telah memilih:")
            for i, it in enumerate(new_selection, start=1):
                st.write(f"{i}. {it['kode']} - {it['nama']}")
        else:
            st.write("Belum ada pilihan.")

        return taxonomy


# =========================
# OpenAI (opsional)
# =========================

def get_gpt_response(prompt, system_message="", model="gpt-4o-mini", temperature=0.7, max_tokens=2000):
    """
    Wrapper OpenAI. Pastikan OPENAI_API_KEY terpasang.
    Ganti model sesuai ketersediaan.
    """
    if not OPENAI_OK:
        raise RuntimeError("OpenAI package tidak tersedia. Install/openai dan set OPENAI_API_KEY.")
    try:
        # API baru (client) — jika kamu pakai SDK v1.x
        # from openai import OpenAI
        # client = OpenAI()
        # resp = client.chat.completions.create(
        #     model=model,
        #     messages=[
        #         {"role": "system", "content": system_message},
        #         {"role": "user", "content": prompt},
        #     ],
        #     temperature=temperature,
        #     max_tokens=max_tokens,
        # )
        # return resp.choices[0].message.content

        # Kompat: ChatCompletion (SDK lama)
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
        raise RuntimeError(f"Error GPT: {e}")


def saran_gpt_metrix_strategi_risiko():
    st.markdown("### 🤖 Saran AI: Metrix Strategi Risiko")

    selected_taxonomies = st.session_state.get("selected_taxonomi", [])
    if not selected_taxonomies:
        st.warning("⚠️ Anda belum memilih taksonomi risiko. Pilih taksonomi terlebih dahulu.")
        return

    if st.button("🔍 Dapatkan Saran AI"):
        progress = st.progress(0, text="📡 Menyiapkan permintaan ke AI...")

        try:
            progress.progress(20, "📄 Menyusun prompt...")
            prompt = f"""
            Berikut adalah daftar kategori risiko yang dipilih pengguna:

            {json.dumps(selected_taxonomies, indent=2, ensure_ascii=False)}

            TUGAS:
            - WAJIB berikan output untuk setiap item di atas (tanpa ada yang terlewat).
            - Balas HANYA JSON array valid: [{{...}}, {{...}}]
            - Kolom wajib:
                - "Kode Risiko"
                - "Kategori Risiko T2 & T3 KBUMN"
                - "Risk Appetite Statement"
                - "Sikap Terhadap Risiko" (salah satu: "Strategis", "Moderat", "Konservatif", "Tidak toleran")
                - "Parameter"
                - "Satuan Ukuran"
                - "Nilai Batasan/Limit"
            - Tanpa narasi di luar JSON.
            """

            progress.progress(45, "🧠 Menghubungi GPT...")
            ai_text = get_gpt_response(
                prompt,
                system_message="Anda adalah asisten AI yang membantu analisis risiko.",
                temperature=0.5,
                max_tokens=4000
            )

            progress.progress(60, "📥 Parsing respons AI...")
            recommended_data = extract_json(ai_text)
            if not recommended_data:
                raise ValueError("Respons AI tidak valid atau tidak mengandung JSON array.")

            expected_cols = [
                "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN",
                "Risk Appetite Statement", "Sikap Terhadap Risiko",
                "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit",
            ]
            df_rec = pd.DataFrame.from_records(recommended_data)
            miss = [c for c in expected_cols if c not in df_rec.columns]
            if miss:
                raise ValueError(f"Kolom wajib hilang: {miss}")

            valid_attitudes = {"Strategis", "Moderat", "Konservatif", "Tidak toleran"}
            df_rec["Sikap Terhadap Risiko"] = df_rec["Sikap Terhadap Risiko"].apply(
                lambda x: x if str(x) in valid_attitudes else "Moderat"
            ).astype(str)

            df_rec = df_rec.reset_index(drop=True)

            progress.progress(85, "💾 Menyimpan ke session state...")
            st.session_state["metrix_strategi"] = df_rec.copy()
            st.session_state["copy_metrix_strategi_risiko"] = df_rec.copy()

            progress.progress(100, "✅ Selesai")
            st.success("✅ Saran AI berhasil ditambahkan.")
        except Exception as e:
            st.error(f"❌ Kesalahan saat mengambil/parse saran AI: {e}")


# =========================
# Editor Metrix Strategi
# =========================

def modul_metrix_strategi_risiko():
    st.subheader("Modul Metrix Strategi Risiko 📝")

    if "Kode Risiko" not in st.session_state["metrix_strategi"].columns:
        st.session_state["metrix_strategi"]["Kode Risiko"] = ""

    base_cols = [
        "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN",
        "Risk Appetite Statement", "Sikap Terhadap Risiko",
        "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
    ]
    # pastikan semua kolom ada
    for c in base_cols:
        if c not in st.session_state["metrix_strategi"].columns:
            st.session_state["metrix_strategi"][c] = ""

    df_disp = st.session_state["metrix_strategi"][base_cols].copy()
    # tampilkan kolom No (view only)
    df_view = df_disp.copy()
    df_view.insert(0, "No", range(1, len(df_view) + 1))

    edited_view = st.data_editor(
        df_view,
        key="metrix_strategi_editor",
        num_rows="dynamic",
        use_container_width=True
    )

    # drop kolom No saat commit
    edited_df = edited_view.drop(columns=["No"], errors="ignore")

    if st.button("🔄 Update Data", key="update_metrix_strategi"):
        # Simpan hasil edit
        st.session_state["metrix_strategi"] = generate_risk_codes(edited_df)
        st.session_state["copy_metrix_strategi_risiko"] = st.session_state["metrix_strategi"].copy()
        st.success("✅ Data 'Metrix Strategi Risiko' berhasil diperbarui & diberi Kode Risiko otomatis.")


# =========================
# Save & Download Excel
# =========================

def save_and_download_strategi_risiko_combined():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    kode_perusahaan = st.session_state.get("kode_perusahaan", "Unknown")

    # Tentukan path file yang aman per user
    file_name = f"Strategi_Risiko_{kode_perusahaan}_{timestamp}.xlsx"
    server_file_path = get_user_file(file_name)  # gunakan utils bawaan app

    df_copy_ambang = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame())
    if not isinstance(df_copy_ambang, pd.DataFrame):
        df_copy_ambang = pd.DataFrame(columns=["Ambang Batas", "Nilai"])

    limit_value = st.session_state.get("copy_limit_risiko", "-")
    df_limit = pd.DataFrame([{"Limit Risiko": limit_value}])

    df_metrix_copy = st.session_state.get("copy_metrix_strategi_risiko", pd.DataFrame())
    if not isinstance(df_metrix_copy, pd.DataFrame):
        df_metrix_copy = pd.DataFrame(columns=[
            "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN", "Risk Appetite Statement",
            "Sikap Terhadap Risiko", "Parameter", "Satuan Ukuran", "Nilai Batasan/Limit"
        ])

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
            file_name=os.path.basename(server_file_path),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Gagal menyimpan file: {e}")


# =========================
# MAIN
# =========================

def main():
    st.title("📊 Strategi Risiko - Upload & Analisa Data")
    init_state()

    # Upload Excel
    uploaded_file = st.file_uploader("📥 Pilih file Excel", type=["xls", "xlsx"], key="data_uploader")

    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file, engine="openpyxl")
            sheet_names = [s.strip() for s in xls.sheet_names]

            expected_strategi = [
                "Copy Ambang Batas Risiko",
                "Copy Limit Risiko",
                "Copy Metrix Strategi Risiko",
            ]

            profil_sheets, strategi_sheets = [], []
            for s in sheet_names:
                (strategi_sheets if s in expected_strategi else profil_sheets).append(s)

            # Profil Perusahaan
            if profil_sheets:
                profil_data = {}
                for s in profil_sheets:
                    df = xls.parse(s)
                    profil_data[s.lower().replace(" ", "_")] = df.copy()
                st.session_state["copy2_profil_perusahaan"] = profil_data
                st.success(f"✅ Data Profil Perusahaan berhasil dimuat ({len(profil_data)} tabel).")

            # Strategi Risiko
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
                st.success(f"✅ Data Strategi Risiko berhasil dimuat ({len(strategi_sheets)} sheet).")

            unknown = [s for s in sheet_names if s not in (profil_sheets + strategi_sheets)]
            if unknown:
                st.warning(f"⚠️ Sheet tidak dikenali & di-skip: {', '.join(unknown)}")

        except Exception as e:
            st.error(f"❌ Gagal memuat data: {e}")

    # Profil Perusahaan → tarik kode & total aset
    profil = st.session_state.get("copy2_profil_perusahaan", {})
    informasi_perusahaan_df = profil.get("informasi_perusahaan", pd.DataFrame())

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
                    st.session_state["kode_perusahaan"] = str(kode_row.iloc[0]["Input Pengguna"]).strip()
                if not aset_row.empty:
                    total_aset_dari_profil = parse_int_like(aset_row.iloc[0]["Input Pengguna"])
            except Exception as e:
                st.warning(f"⚠️ Gagal baca profil perusahaan: {e}")

            for _, row in informasi_perusahaan_df.iterrows():
                st.markdown(f"**{str(row.get('Data yang dibutuhkan','')).strip()}**: {str(row.get('Input Pengguna','')).strip()}")
        else:
            st.warning("⚠️ Profil perusahaan belum dimuat atau kosong.")

    # Input Total Aset
    st.subheader("💰 Input Total Aset")
    default_aset_str = f"{total_aset_dari_profil:,}".replace(",", ".") if total_aset_dari_profil else ""
    total_aset_input = st.text_input("Total Aset:", value=default_aset_str, placeholder="Contoh: 13.000.000.000.000")
    total_aset_val = parse_int_like(total_aset_input)

    # Ambang Batas Risiko (editor)
    st.write("### 📊 Ambang Batas Risiko")
    df_ambang = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame())
    if df_ambang.empty:
        df_ambang = pd.DataFrame({
            "Ambang Batas": ["Total Aset", "Risk Capacity", "Risk Appetite", "Risk Tolerance", "Limit Risiko"],
            "Nilai": ["-", "-", "-", "-", "-"],
        })
    df_view = df_ambang.reset_index(drop=True).copy()
    df_view.insert(0, "No", range(1, len(df_view) + 1))

    edited_amb = st.data_editor(
        df_view[["Ambang Batas", "Nilai"]],
        key="editor_ambang_batas",
        num_rows="fixed",
        hide_index=True
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Update Data"):
            if not edited_amb.empty:
                # commit ke state (tanpa kolom No)
                df_ambang_update = edited_amb.copy()
                st.session_state["copy_ambang_batas_risiko"] = df_ambang_update
                # Update limit jika ada
                baris_limit = df_ambang_update[df_ambang_update["Ambang Batas"] == "Limit Risiko"]
                if not baris_limit.empty:
                    st.session_state["copy_limit_risiko"] = parse_int_like(baris_limit["Nilai"].values[0]) or baris_limit["Nilai"].values[0]
                st.success("✅ Data Ambang Batas Risiko berhasil diperbarui.")
            else:
                st.warning("⚠️ Belum ada data untuk disalin.")
    with col2:
        if st.button("📊 Hitung Ambang Batas"):
            if not total_aset_val:
                st.error("❌ Total Aset tidak valid. Masukkan angka yang benar.")
            else:
                hasil, limit_risk = modul_ambang_batas(total_aset_val)
                if hasil is not None:
                    # Gabungkan dengan edit user bila ada
                    try:
                        merged = hasil.copy()
                        # override jika user sudah mengisi manual
                        for i, row in merged.iterrows():
                            ambang = row["Ambang Batas"]
                            if ambang in edited_amb["Ambang Batas"].values:
                                val_user = edited_amb.loc[edited_amb["Ambang Batas"] == ambang, "Nilai"].values[0]
                                merged.at[i, "Nilai"] = val_user
                    except Exception:
                        merged = hasil
                        st.info("ℹ️ Tekan '📋 Update Data' terlebih dahulu jika ingin mempertahankan editan manual.")
                    st.session_state["copy_ambang_batas_risiko"] = merged[["Ambang Batas", "Nilai"]].copy()
                    st.session_state["copy_limit_risiko"] = limit_risk
                    st.success("✅ Ambang Batas dihitung & digabung dengan editan pengguna.")

    # Final table
    st.markdown("### 📌 Tabel Ambang Batas Risiko (Final)")
    df_final = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame()).copy()
    if isinstance(df_final, pd.DataFrame) and not df_final.empty:
        st.dataframe(df_final.reset_index(drop=True), hide_index=True, use_container_width=True)
    else:
        st.info("📭 Belum ada data ambang batas final. Isi manual atau klik **Hitung Ambang Batas**.")

    if st.button("📋 Simpan Ulang dari Tabel Final"):
        if not edited_amb.empty:
            st.session_state["copy_ambang_batas_risiko"] = edited_amb.copy()
            baris_limit = edited_amb[edited_amb["Ambang Batas"] == "Limit Risiko"]
            if not baris_limit.empty:
                st.session_state["copy_limit_risiko"] = parse_int_like(baris_limit["Nilai"].values[0]) or baris_limit["Nilai"].values[0]
            st.success("✅ Data Ambang Batas Risiko disalin dari editor.")
        else:
            st.warning("⚠️ Belum ada data untuk disalin.")

    # Modul lanjut
    tampilkan_taksonomi_risiko_relevan()
    saran_gpt_metrix_strategi_risiko()
    modul_metrix_strategi_risiko()

    save_and_download_strategi_risiko_combined()


if __name__ == "__main__":
    main()
