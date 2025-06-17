import streamlit as st
import pandas as pd
from modules.utils import get_user_file
from datetime import datetime
import io
import os

# Fungsi bantu untuk memberi label nama file yang ramah pengguna
def identifikasi_jenis_file(sheet_names):
    sn = [s.lower() for s in sheet_names]
    if "pendapatan_bisnis_rutin" in sn and "biaya_rutin_bisnis_rutin" in sn:
        return "📁 Profil Perusahaan"
    elif "copy limit risiko" in sn:
        return "📁 Strategi Risiko"
    elif "residual_prob" in sn and "residual_dampak" in sn:
        return "📁 Residual Risiko"
    elif "total biaya" in sn:
        return "📁 Perlakuan Risiko"
    elif "ambang batas risiko" in sn:
        return "📁 Ekspor RBB"
    else:
        return "📁 File Tidak Dikenali"

# Fungsi utama
def load_data_rbb_dari_file():
    with st.expander("📥 Silakan Upload 3 file:  Profil_Perusahaan, perlakuan_risiko,Residual_Dampak,)", expanded=True):
        uploaded_files = st.file_uploader("Unggah hingga 4-5 file Excel", type=["xlsx"], accept_multiple_files=True)

        if not uploaded_files:
            st.info("📄 Silakan unggah file Excel.")
            return

        for file in uploaded_files:
            try:
                xls = pd.ExcelFile(file)
                sheet_names = [s.lower() for s in xls.sheet_names]
                jenis_file = identifikasi_jenis_file(sheet_names)
                st.markdown(f"✅ **Memproses:** {jenis_file}")

                # 🔁 File Ekspor RBB
                if "ambang batas risiko" in sheet_names:
                    st.session_state["copy_ambang_batas_risiko"] = xls.parse("Ambang Batas Risiko")
                if "ringkasan rbb" in sheet_names:
                    st.session_state["copy_summary_rbb"] = xls.parse("Summary RBB")
                if "rasio keuangan" in sheet_names:
                    st.session_state["copy_rasio_keuangan"] = xls.parse("Rasio Keuangan")

                # 📊 Profil perusahaan
                if "pendapatan_bisnis_rutin" in sheet_names:
                    st.session_state["copy_pendapatan_bisnis_rutin"] = xls.parse("pendapatan_bisnis_rutin")
                if "pendapatan_bisnis_baru" in sheet_names:
                    st.session_state["copy_pendapatan_bisnis_baru"] = xls.parse("pendapatan_bisnis_baru")
                if "biaya_rutin_bisnis_rutin" in sheet_names:
                    st.session_state["copy_biaya_rutin_bisnis_rutin"] = xls.parse("biaya_rutin_bisnis_rutin")
                if "biaya_non_rutin_bisnis_baru" in sheet_names:
                    st.session_state["copy_biaya_non_rutin_bisnis_baru"] = xls.parse("biaya_non_rutin_bisnis_baru")

                # 📈 Strategi risiko
                if "copy ambang batas risiko" in sheet_names:
                    st.session_state["copy_ambang_batas_risiko"] = xls.parse("Copy Ambang Batas Risiko")
                if "copy limit risiko" in sheet_names:
                    limit_df = xls.parse("Copy Limit Risiko")
                    try:
                        nilai_kandidat = limit_df.select_dtypes(include='number')
                        if not nilai_kandidat.empty:
                            nilai_limit = nilai_kandidat.iloc[0, 0]
                            if "copy_limit_risiko" not in st.session_state:
                                st.session_state["copy_limit_risiko"] = nilai_limit
                                formatted = f"Rp {nilai_limit:,.0f}".replace(",", ".")
                                st.success(f"✅ Limit Risiko berhasil diambil: **{formatted}**")
                            else:
                                st.info("ℹ️ Limit Risiko sudah ada, tidak ditimpa.")
                        else:
                            st.warning("❗ Tidak ada kolom numerik untuk Limit Risiko.")
                    except Exception as e:
                        st.error(f"❌ Gagal membaca Limit Risiko: {e}")


                # 📉 Residual risiko
                if "residual_prob" in sheet_names:
                    st.session_state["copy_residual_pendapatan"] = xls.parse("residual_prob")
                if "residual_dampak" in sheet_names:
                    st.session_state["copy_residual_biaya"] = xls.parse("residual_dampak")
                if "residual_eksposur" in sheet_names:
                    st.session_state["copy_residual_eksposur"] = xls.parse("residual_eksposur")

                # 🛠️ Perlakuan risiko
                if "total biaya" in sheet_names:
                    df_biaya_mitigasi = xls.parse("Total Biaya")
                    if "Total Biaya Perlakuan Risiko" in df_biaya_mitigasi.columns:
                        st.session_state["copy_total_biaya_mitigasi"] = df_biaya_mitigasi["Total Biaya Perlakuan Risiko"].sum()
                        st.success("✅ Total biaya mitigasi berhasil diambil.")
                    else:
                        st.warning("❗ Kolom 'Total Biaya Perlakuan Risiko' tidak ditemukan di sheet Total Biaya.")

            except Exception as e:
                st.error(f"❌ Gagal memproses file: **{file.name}**. Error: {e}")

# Fungsi pembantu untuk mengambil nilai dari session state
def get_total_from_session(key):
    value = st.session_state.get(key)
    if isinstance(value, pd.DataFrame):
        if "Nilai" in value.columns:
            return value["Nilai"].sum()
        else:
            numeric_cols = value.select_dtypes(include=['number'])
            return numeric_cols.sum().sum() if not numeric_cols.empty else 0
    elif isinstance(value, (int, float)):
        return value
    else:
        return 0

def tampilkan_tabel_ambang_batas():
    df_ambang = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame())
    if isinstance(df_ambang, pd.DataFrame) and not df_ambang.empty:
        df_formatted = df_ambang.copy()
        if "Nilai" in df_formatted.columns:
            df_formatted["Nilai"] = df_formatted["Nilai"].apply(lambda x: f"Rp {x:,.0f}".replace(",", "."))
        df_formatted.insert(0, "No", range(1, len(df_formatted) + 1))  # Tambah nomor
        st.subheader("📊 Tabel Ambang Batas Risiko")
        st.dataframe(df_formatted, use_container_width=False, hide_index=True)
    else:
        st.warning("⚠️ Tabel ambang batas risiko belum tersedia di session_state.")


def evaluasi_limit_risiko():
    st.subheader("📊 Analisa: Evaluasi Limit Risiko")
    limit_risiko = st.session_state.get("copy_limit_risiko", 0)

    # Konversi eksplisit ke float untuk menghindari masalah tipe data seperti numpy.int64
    try:
        limit_risiko = float(limit_risiko)
    except (ValueError, TypeError):
        limit_risiko = 0

    if pd.isna(limit_risiko) or limit_risiko <= 0:
        st.warning("⚠️ Limit Risiko tidak valid atau tidak ditemukan.")
        limit_risiko = 0

    eksposur_pendapatan = -abs(get_total_from_session("copy_residual_pendapatan"))
    eksposur_biaya = -abs(get_total_from_session("copy_residual_biaya"))
    total_eksposur = abs(eksposur_pendapatan + eksposur_biaya)

    formatted_limit = f"Rp {limit_risiko:,.0f}".replace(",", ".")
    formatted_eksposur = f"Rp {total_eksposur:,.0f}".replace(",", ".")

    st.markdown(f"**Limit Risiko**: {formatted_limit}")
    st.markdown(f"**Total Eksposur Risiko Residual (Pendapatan + Biaya)**: {formatted_eksposur}")
    if total_eksposur > limit_risiko:
        st.error("⚠️ Total Eksposur melebihi Limit Risiko! Perlu evaluasi lebih lanjut.")
    else:
        st.success("✅ Total Eksposur masih berada di bawah Limit Risiko.")


def tampilkan_rasio_keuangan(data):
    # Rasio dan nilainya
    ratios = {
        "Gross Profit Margin": data["Target Laba Sebelum Pajak"] / data["Total Proyeksi Pendapatan"],
        "Cost Ratio": abs(data["Total Biaya"]) / data["Total Proyeksi Pendapatan"],
        "Risk Impact to Revenue Ratio": abs(data["Eksposur Risiko Residual yang Berdampak pada Pendapatan"]) / data["Total Proyeksi Pendapatan"],
        "Risk Impact to Cost Ratio": abs(data["Eksposur Risiko Residual yang Berdampak pada Biaya"]) / abs(data["Total Biaya"]),
        "Mitigation Cost to Total Cost Ratio": abs(data["Biaya Mitigasi Risiko"]) / abs(data["Total Biaya"]),
        "Total Eksposur Residual terhadap Limit Risiko":
            (abs(data["Eksposur Risiko Residual yang Berdampak pada Pendapatan"]) + abs(data["Eksposur Risiko Residual yang Berdampak pada Biaya"]))
            / st.session_state.get("copy_limit_risiko", 1)
    }

    # Standar ideal (dalam persen)
    ratio_standards = {
        "Gross Profit Margin": 0.30,
        "Cost Ratio": 0.70,
        "Risk Impact to Revenue Ratio": 0.10,
        "Risk Impact to Cost Ratio": 0.10,
        "Mitigation Cost to Total Cost Ratio": 0.10,
        "Total Eksposur Residual terhadap Limit Risiko": 1.00
    }

    # Rasio yang lebih bagus jika nilainya kecil
    rasio_negatif = [
        "Cost Ratio",
        "Risk Impact to Revenue Ratio",
        "Risk Impact to Cost Ratio",
        "Mitigation Cost to Total Cost Ratio",
        "Total Eksposur Residual terhadap Limit Risiko"
    ]

    # Penjelasan tiap rasio
    penjelasan = {
        "Gross Profit Margin": "Rasio antara laba sebelum pajak terhadap total pendapatan. Semakin tinggi semakin baik.",
        "Cost Ratio": "Rasio biaya total terhadap pendapatan. Semakin rendah semakin efisien.",
        "Risk Impact to Revenue Ratio": "Dampak risiko residual terhadap pendapatan. Nilai tinggi menunjukkan risiko besar terhadap pendapatan.",
        "Risk Impact to Cost Ratio": "Dampak risiko residual terhadap biaya. Nilai tinggi menunjukkan potensi pembengkakan biaya.",
        "Mitigation Cost to Total Cost Ratio": "Perbandingan biaya mitigasi terhadap total biaya. Semakin rendah semakin efisien.",
        "Total Eksposur Residual terhadap Limit Risiko": "Total risiko residual dibandingkan dengan limit risiko yang ditetapkan. Nilai > 1 menunjukkan melebihi batas."
    }

    # Buat DataFrame rasio
    ratios_df = pd.DataFrame(
        [(key, val * 100, ratio_standards[key] * 100, penjelasan[key]) for key, val in ratios.items()],
        columns=["Rasio Keuangan", "Nilai (%)", "Nilai Standar (%)", "Penjelasan"]
    )
    ratios_df.insert(0, "No", range(1, len(ratios_df) + 1))

    # Highlight merah jika tidak sesuai standar
    def highlight_conditional(row):
        rasio = row["Rasio Keuangan"]
        nilai = row["Nilai (%)"]
        standar = row["Nilai Standar (%)"]
        color = 'background-color: red; color: white;'
        styles = [''] * len(row)
        idx_nilai = ratios_df.columns.get_loc("Nilai (%)")

        if rasio in rasio_negatif and nilai > standar:
            styles[idx_nilai] = color
        elif rasio not in rasio_negatif and nilai < standar:
            styles[idx_nilai] = color

        return styles

    # Simpan ke session
    st.session_state["copy_rasio_keuangan"] = ratios_df

    # Tampilkan
    st.write("### 📈 Rasio Keuangan")
    st.dataframe(
        ratios_df.style
            .format({"Nilai (%)": "{:.2f}%", "Nilai Standar (%)": "{:.2f}%"})
            .apply(highlight_conditional, axis=1),
        use_container_width=True,
        hide_index=True
    )

def save_tabel_rbb_terpilih_dengan_download(judul="risk_based_budgeting"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_path = "C:/saved"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filename = f"{judul}_{timestamp}.xlsx"
    server_file_path = os.path.join(folder_path, filename)
    output = io.BytesIO()

    df_ambang = st.session_state.get("copy_ambang_batas_risiko", pd.DataFrame())
    df_summary = st.session_state.get("copy_summary_rbb", pd.DataFrame())
    df_rasio = st.session_state.get("copy_rasio_keuangan", pd.DataFrame())

    if df_ambang.empty and df_summary.empty and df_rasio.empty:
        st.warning("⚠️ Tidak ada data yang tersedia untuk disimpan.")
        return

    with pd.ExcelWriter(server_file_path, engine="xlsxwriter") as writer_server, \
         pd.ExcelWriter(output, engine="xlsxwriter") as writer_download:

        for sheet_name, df in {
            "Ambang Batas Risiko": df_ambang,
            "Summary RBB": df_summary,
            "Rasio Keuangan": df_rasio
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
        label="⬇️ Unduh File RBB",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def main():
    st.title("📊 Risk Based Budgeting")

    # Langkah 1: Upload dan muat semua data
    load_data_rbb_dari_file()

    # Jika data belum lengkap, jangan lanjut
    required_keys = [
        "copy_pendapatan_bisnis_rutin", "copy_pendapatan_bisnis_baru",
        "copy_residual_pendapatan", "copy_biaya_rutin_bisnis_rutin",
        "copy_biaya_non_rutin_bisnis_baru", "copy_residual_biaya",
        "copy_total_biaya_mitigasi", "copy_limit_risiko"
    ]
    if not all(k in st.session_state for k in required_keys):
        st.warning("⚠️ Data belum lengkap. Silakan unggah semua file yang diperlukan.")
        st.stop()

    # Langkah 2: Ambil nilai dari session state
    proyeksi_pendapatan_bisnis_rutin = get_total_from_session("copy_pendapatan_bisnis_rutin")
    proyeksi_pendapatan_bisnis_baru = get_total_from_session("copy_pendapatan_bisnis_baru")
    eksposur_residual_pendapatan = -abs(get_total_from_session("copy_residual_pendapatan"))
    total_proyeksi_pendapatan = proyeksi_pendapatan_bisnis_rutin + proyeksi_pendapatan_bisnis_baru + eksposur_residual_pendapatan

    biaya_rutin = -abs(get_total_from_session("copy_biaya_rutin_bisnis_rutin"))
    biaya_non_rutin = -abs(get_total_from_session("copy_biaya_non_rutin_bisnis_baru"))
    eksposur_residual_biaya = -abs(get_total_from_session("copy_residual_biaya"))
    biaya_mitigasi = -abs(st.session_state.get("copy_total_biaya_mitigasi", 0))

    total_biaya = biaya_rutin + biaya_non_rutin + eksposur_residual_biaya + biaya_mitigasi
    target_laba = total_proyeksi_pendapatan + total_biaya

    # Langkah 3: Summary RBB
    final_summary_data = {
        "Proyeksi Pendapatan Bisnis Rutin": proyeksi_pendapatan_bisnis_rutin,
        "Proyeksi Pendapatan atas Strategi Bisnis Baru": proyeksi_pendapatan_bisnis_baru,
        "Eksposur Risiko Residual yang Berdampak pada Pendapatan": eksposur_residual_pendapatan,
        "Total Proyeksi Pendapatan": total_proyeksi_pendapatan,
        "Biaya Rutin untuk Pencapaian Pendapatan Bisnis Rutin": biaya_rutin,
        "Biaya Non Rutin untuk Pencapaian Pendapatan atas Strategi Bisnis Baru": biaya_non_rutin,
        "Eksposur Risiko Residual yang Berdampak pada Biaya": eksposur_residual_biaya,
        "Biaya Mitigasi Risiko": biaya_mitigasi,
        "Total Biaya": total_biaya,
        "Target Laba Sebelum Pajak": target_laba
    }

    summary_df = pd.DataFrame(
        list(final_summary_data.items()),
        columns=["Kategori", "Nilai"]
    )
    summary_df.insert(0, "No", range(1, len(summary_df) + 1))

    # Langkah 4: Tampilkan hasil
    tampilkan_tabel_ambang_batas()
    st.write("### 📋 Ringkasan Risk-Based Budgeting")
    st.dataframe(summary_df.style.format({"Nilai": "{:,.0f}"}), use_container_width=True, hide_index=True)

    evaluasi_limit_risiko()
    tampilkan_rasio_keuangan(final_summary_data)

    # Langkah 5: Simpan ke session & ekspor
    if st.button("🔁 Update Data"):
        st.session_state["copy_summary_rbb"] = summary_df
        st.success("✅ Summary RBB berhasil disimpan ke session state.")

    save_tabel_rbb_terpilih_dengan_download(judul="risk_based_budgeting")


if __name__ == "__main__":
    main()
