import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

def upload_file_gabungan_fleksibel():
    st.markdown("### 📥 Upload File Gabungan Risiko")
    uploaded_files = st.file_uploader(
        "Unggah file (.xlsx) yang berisi Strategi, Inherent, dan/atau Residual Risiko",
        type=["xlsx"],
        accept_multiple_files=True,
        key="upload_file_gabungan_fleksibel"
    )

    if uploaded_files:
        st.info("✅ File berhasil diunggah. Klik tombol **📤 Proses Data** untuk membaca isi file.")

        if st.button("📤 Proses Data"):
            for file in uploaded_files:
                try:
                    xls = pd.ExcelFile(file)
                    sheet_names = [s.lower() for s in xls.sheet_names]

                    # === Deteksi dan simpan strategi
                    if any("strategi" in file.name.lower() or "aset" in s for s in sheet_names):
                        for sheet in xls.sheet_names:
                            df_sheet = pd.read_excel(xls, sheet_name=sheet)
                            baris_limit = df_sheet[df_sheet.iloc[:, 0].astype(str).str.lower().str.contains("limit risiko", na=False)]
                            if not baris_limit.empty:
                                nilai_limit = pd.to_numeric(baris_limit.iloc[0, 1], errors='coerce')
                                st.session_state["copy_limit_risiko"] = nilai_limit
                                st.success(f"✅ Limit Risiko berhasil dimuat dari: {file.name}")

                    # === Inherent Risiko
                    if "tabel kuantitatif" in sheet_names:
                        st.session_state["copy_Risiko_Kuantitatif"] = pd.read_excel(xls, sheet_name="Tabel Kuantitatif")
                        st.success(f"✅ Risiko Kuantitatif dimuat dari: {file.name}")
                    if "tabel kualitatif" in sheet_names:
                        st.session_state["copy_Risiko_Kualitatif"] = pd.read_excel(xls, sheet_name="Tabel Kualitatif")
                        st.success(f"✅ Risiko Kualitatif dimuat dari: {file.name}")

                    # === Residual Risiko (jika hasil ekspor sebelumnya)
                    if "residual_dampak" in sheet_names:
                        st.session_state["copy_tabel_residual_dampak"] = pd.read_excel(xls, sheet_name="residual_dampak")
                    if "residual_prob" in sheet_names:
                        st.session_state["copy_tabel_residual_probabilitas"] = pd.read_excel(xls, sheet_name="residual_prob")
                    if "residual_eksposur" in sheet_names:
                        st.session_state["copy_tabel_residual_eksposur"] = pd.read_excel(xls, sheet_name="residual_eksposur")

                    # Hitung total Q4 otomatis jika lengkap
                    if all(k in st.session_state for k in ["copy_tabel_residual_dampak", "copy_tabel_residual_probabilitas", "copy_tabel_residual_eksposur"]):
                        df_eksposur = st.session_state["copy_tabel_residual_eksposur"]
                        if 'Dampak Anggaran' in df_eksposur.columns and any(col.startswith("Nilai Q4") for col in df_eksposur.columns):
                            q4_col = [col for col in df_eksposur.columns if col.startswith("Nilai Q4")][0]
                            total_df = df_eksposur[['Dampak Anggaran', q4_col]].copy()
                            total_df[q4_col] = pd.to_numeric(total_df[q4_col], errors='coerce')
                            total_q4_dict = total_df.groupby('Dampak Anggaran')[q4_col].sum().to_dict()
                            st.session_state["copy_residual_biaya"] = total_q4_dict.get("Biaya", 0.0)
                            st.session_state["copy_residual_pendapatan"] = total_q4_dict.get("Pendapatan", 0.0)
                            st.success(f"✅ File residual dimuat lengkap dari: {file.name}")
                except Exception as e:
                    st.error(f"❌ Gagal memproses file {file.name}: {e}")
    else:
        st.info("📁 Belum ada file yang diunggah.")

# Tabel Residual Probabilitas
def buat_tabel_residual_probabilitas(df_gabungan):
    kolom_skala = ["Skala Q1", "Skala Q2", "Skala Q3", "Skala Q4",
                   "Skala KBUMN Q1", "Skala KBUMN Q2", "Skala KBUMN Q3", "Skala KBUMN Q4"]

    if {'Kode Risiko', 'Peristiwa Risiko', 'Nilai Probabilitas'}.issubset(df_gabungan.columns):
        # Bersihkan dan konversi nilai probabilitas
        df_gabungan['Nilai Probabilitas'] = (
            df_gabungan['Nilai Probabilitas']
            .astype(str)
            .str.replace("%", "", regex=False)
            .str.strip()
        )
        df_gabungan['Nilai Probabilitas'] = pd.to_numeric(df_gabungan['Nilai Probabilitas'], errors='coerce') / 100

        # Tampilkan peringatan jika ada nilai error
        baris_invalid = df_gabungan[df_gabungan['Nilai Probabilitas'].isnull()]
        if not baris_invalid.empty:
            st.warning("⚠️ Beberapa 'Nilai Probabilitas' tidak valid dan akan diabaikan.")
            st.dataframe(baris_invalid[['Kode Risiko', 'Peristiwa Risiko', 'Nilai Probabilitas']])

        # Buat dataframe hasil
        df = pd.DataFrame()
        df['Kode Risiko'] = df_gabungan['Kode Risiko']
        df['Peristiwa Risiko'] = df_gabungan['Peristiwa Risiko']
        df['Kategori Risiko T2 & T3 KBUMN'] = df_gabungan.get("Kategori Risiko T2 & T3 KBUMN", "")
        df['Probabilitas (%)'] = (df_gabungan['Nilai Probabilitas'] * 100).round(2).astype(str) + '%'

        # Hitung Nilai Q1-Q4 dan Skala
        for q, faktor in zip(['Q1', 'Q2', 'Q3', 'Q4'], [0.9, 0.8, 0.5, 0.1]):
            df[f'Nilai {q}'] = df_gabungan['Nilai Probabilitas'] * faktor
            df[f'Skala {q}'] = df[f'Nilai {q}'].apply(hitung_skala_probabilitas)

        # Tambahkan kolom kosong untuk KBUMN
        for q in ['Q1', 'Q2', 'Q3', 'Q4']:
            df[f'Skala KBUMN {q}'] = ""

        # Tambahkan kolom nomor urut
        df.insert(0, "Nomor", range(1, len(df) + 1))
        return df
    else:
        st.warning("❌ Kolom 'Kode Risiko', 'Peristiwa Risiko', atau 'Nilai Probabilitas' tidak ditemukan.")
        return pd.DataFrame()

   

def buat_tabel_residual_dari_gabungan(df_gabungan):
    kolom_skala = [
        "Skala Q1", "Skala Q2", "Skala Q3", "Skala Q4",
        "Skala KBUMN Q1", "Skala KBUMN Q2", "Skala KBUMN Q3", "Skala KBUMN Q4"
    ]
    limit = st.session_state.get("copy_limit_risiko", 0)

    if 'Kode Risiko' in df_gabungan.columns and 'Peristiwa Risiko' in df_gabungan.columns:

        if 'Nilai Dampak' not in df_gabungan.columns:
            st.warning("⚠️ Kolom 'Nilai Dampak' tidak ditemukan, kolom akan dibuat dengan nilai 0.")
            df_gabungan['Nilai Dampak'] = 0

        # ✅ Konversi aman dari format Indonesia (1.500,00 → 1500.00)
        # Parsing format Indonesia
        nilai_dampak_bersih = (
            df_gabungan['Nilai Dampak']
            .astype(str)
            .str.replace(r"\.", "", regex=True)   # hapus titik ribuan
            .str.replace(r",", ".", regex=True)   # ubah koma jadi titik desimal
        )
        df_gabungan['Nilai Dampak'] = pd.to_numeric(nilai_dampak_bersih, errors='coerce')

        # Isi NaN dengan 0
        df_gabungan['Nilai Dampak'] = df_gabungan['Nilai Dampak'].fillna(0)

        # Buat DataFrame hasil
        df = pd.DataFrame()
        df['Kode Risiko'] = df_gabungan['Kode Risiko']
        df['Peristiwa Risiko'] = df_gabungan['Peristiwa Risiko']
        df['Kategori Risiko T2 & T3 KBUMN'] = df_gabungan.get("Kategori Risiko T2 & T3 KBUMN", "")
        df['Nilai Dampak'] = df_gabungan['Nilai Dampak'] / 10   # 🔥 Koreksi langsung di sini
        df['Dampak Anggaran'] = df_gabungan.get('Dampak Anggaran', "")

        # Hitung nilai Q1-Q4 dan skala
        for q, faktor in zip(['Q1', 'Q2', 'Q3', 'Q4'], [0.9, 0.8, 0.5, 0.1]):
            df[f'Nilai {q}'] = df['Nilai Dampak'] * faktor
            df[f'Skala {q}'] = df[f'Nilai {q}'].apply(lambda x: hitung_skala_dampak(x, limit))

        # Tambahkan kolom kosong untuk skala KBUMN
        for q in ['Q1', 'Q2', 'Q3', 'Q4']:
            df[f'Skala KBUMN {q}'] = ""

        # Tambahkan kolom Nomor
        df.insert(0, "Nomor", range(1, len(df) + 1))


        return df

    else:
        st.warning("❌ Kolom 'Kode Risiko' atau 'Peristiwa Risiko' tidak ditemukan.")
        return pd.DataFrame()



# Fungsi Hitung Skala Dampak (berdasarkan limit)
def hitung_skala_dampak(nilai, limit):
    if limit == 0:
        return 0
    persen = (nilai / limit) * 100
    if persen < 20:
        return 1
    elif persen < 40:
        return 2
    elif persen < 60:
        return 3
    elif persen < 80:
        return 4
    elif persen <= 1000:
        return 5
    else:
        return 0

def hitung_skala_probabilitas(probabilitas_dalam_desimal):
    persen = probabilitas_dalam_desimal * 100
    if persen <= 20:
        return 1
    elif persen <= 40:
        return 2
    elif persen <= 60:
        return 3
    elif persen <= 80:
        return 4
    elif persen <= 100:
        return 5
    else:
        return 0  # fallback untuk nilai tak terduga

def buat_tabel_eksposur_risiko(df_dampak, df_probabilitas, df_gabungan):
    if df_dampak.empty or df_probabilitas.empty:
        st.warning("Data dampak atau probabilitas kosong.")
        return pd.DataFrame()

    # Mapping Matriks Risiko
    mapping_level_risiko = {
        (1, 1): (1, "Hijau Tua"), (2, 1): (2, "Hijau Tua"), (3, 1): (3, "Hijau Tua"),
        (4, 1): (4, "Hijau Tua"), (5, 1): (7, "Hijau Muda"), (1, 2): (5, "Hijau Tua"),
        (2, 2): (6, "Hijau Muda"), (3, 2): (8, "Hijau Muda"), (4, 2): (9, "Hijau Muda"),
        (5, 2): (12, "Kuning"), (1, 3): (10, "Hijau Muda"), (2, 3): (11, "Hijau Muda"),
        (3, 3): (13, "Kuning"), (4, 3): (14, "Kuning"), (5, 3): (17, "Oranye"),
        (1, 4): (15, "Kuning"), (2, 4): (16, "Oranye"), (3, 4): (18, "Oranye"),
        (4, 4): (19, "Oranye"), (5, 4): (22, "Merah"), (1, 5): (20, "Merah"),
        (2, 5): (21, "Merah"), (3, 5): (23, "Merah"), (4, 5): (24, "Merah"), (5, 5): (25, "Merah"),
    }

    # Inisialisasi DataFrame
    df = pd.DataFrame()
    df['Kode Risiko'] = df_dampak['Kode Risiko']
    df['Peristiwa Risiko'] = df_dampak['Peristiwa Risiko']
    df['Kategori Risiko T2 & T3 KBUMN'] = df_dampak.get('Kategori Risiko T2 & T3 KBUMN', "")
    
    # Hitung Nilai Risiko Q1–Q4
    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
        df[f'Nilai {q}'] = df_dampak[f'Nilai {q}'] * df_probabilitas[f'Nilai {q}']

        skala_dampak = df_dampak[f'Skala {q}']
        skala_prob = df_probabilitas[f'Skala {q}']

        skala_risiko = []
        level_risiko = []
        for sd, sp in zip(skala_dampak, skala_prob):
            try:
                key = (int(sp), int(sd))
            except:
                key = (0, 0)
            skala, level = mapping_level_risiko.get(key, (0, "Tidak Diketahui"))
            skala_risiko.append(skala)
            level_risiko.append(level)

        df[f'Skala {q}'] = skala_risiko
        df[f'Skala KBUMN {q}'] = ""  # Placeholder manual
        df[f'Level Risiko {q}'] = level_risiko

    # Tambahkan kolom Nomor
    df.insert(0, "Nomor", range(1, len(df) + 1))

    # Gabungkan kolom Dampak Anggaran (untuk akurasi ekspor & klasifikasi)
    if 'Dampak Anggaran' in df_dampak.columns:
        # Normalize whitespace
        df_dampak['Kode Risiko'] = df_dampak['Kode Risiko'].astype(str).str.strip()
        df_dampak['Peristiwa Risiko'] = df_dampak['Peristiwa Risiko'].astype(str).str.strip()
        df['Kode Risiko'] = df['Kode Risiko'].astype(str).str.strip()
        df['Peristiwa Risiko'] = df['Peristiwa Risiko'].astype(str).str.strip()

        df = df.merge(
            df_dampak[['Kode Risiko', 'Peristiwa Risiko', 'Dampak Anggaran']],
            on=['Kode Risiko', 'Peristiwa Risiko'],
            how='left'
        )
        df['Dampak Anggaran'] = df['Dampak Anggaran'].fillna("")
    else:
        df['Dampak Anggaran'] = ""

    return df
def save_and_download_residual_risk():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_path = "C:/saved"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    server_file_path = os.path.join(folder_path, f"Residual_Dampak_{timestamp}.xlsx")
    output = io.BytesIO()

    df_dampak = st.session_state.get("copy_tabel_residual_dampak", pd.DataFrame())
    df_probabilitas = st.session_state.get("copy_tabel_residual_probabilitas", pd.DataFrame())
    df_eksposur = st.session_state.get("copy_tabel_residual_eksposur", pd.DataFrame())

    if df_dampak.empty or df_probabilitas.empty or df_eksposur.empty:
        st.warning("⚠️ Salah satu dari tabel residual belum tersedia. Tidak bisa menyimpan file.")
        return

    with pd.ExcelWriter(server_file_path, engine='xlsxwriter') as writer_server, \
         pd.ExcelWriter(output, engine='xlsxwriter') as writer_download:
        
        for sheet_name, df in {
            "residual_dampak": df_dampak,
            "residual_prob": df_probabilitas,
            "residual_eksposur": df_eksposur
        }.items():
            df_save = df.copy()
            if "Nomor" in df_save.columns:
                df_save = df_save.drop(columns=["Nomor"])
            df_save.insert(0, "Nomor", range(1, len(df_save) + 1))

            df_save.to_excel(writer_server, sheet_name=sheet_name, index=False)
            df_save.to_excel(writer_download, sheet_name=sheet_name, index=False)

    output.seek(0)

    st.success(f"✅ File berhasil disimpan ke server: `{server_file_path}`")

    st.download_button(
        label="⬇️ Unduh File Residual Risiko",
        data=output,
        file_name=f"Residual_Dampak_{timestamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def tampilkan_tabel():
    st.title("📊 Risiko Residual (Tahap Awal)")

    upload_file_gabungan_fleksibel()

    # Gabungkan data risiko kuantitatif & kualitatif
    if 'copy_Risiko_Kuantitatif' in st.session_state and 'copy_Risiko_Kualitatif' in st.session_state:
        df_q = st.session_state['copy_Risiko_Kuantitatif'].copy()
        df_k = st.session_state['copy_Risiko_Kualitatif'].copy()
        df_q['Tipe Risiko'] = 'Kuantitatif'
        df_k['Tipe Risiko'] = 'Kualitatif'
        df_gabungan = pd.concat([df_q, df_k], ignore_index=True)
    else:
        df_gabungan = None

    # Tampilan tabel awal
    with st.expander("📂 Lihat Data Risiko Awal (Kuantitatif, Kualitatif, dan Gabungan)", expanded=False):
        risiko_q = st.session_state.get('copy_Risiko_Kuantitatif')
        risiko_k = st.session_state.get('copy_Risiko_Kualitatif')
        limit_risiko = st.session_state.get('copy_limit_risiko')

        if risiko_q is not None:
            st.markdown("### 📊 Risiko Kuantitatif")
            st.dataframe(risiko_q, use_container_width=True)
        else:
            st.info("ℹ️ Data Risiko Kuantitatif belum tersedia.")

        if risiko_k is not None:
            st.markdown("### 📊 Risiko Kualitatif")
            st.dataframe(risiko_k, use_container_width=True)
        else:
            st.info("ℹ️ Data Risiko Kualitatif belum tersedia.")

        if df_gabungan is not None:
            st.markdown("### 📊 Gabungan Risiko")
            st.dataframe(df_gabungan, use_container_width=True)
        else:
            st.info("ℹ️ Data Gabungan Risiko belum tersedia.")

        if limit_risiko is not None:
            st.subheader("📌 Limit Risiko")
            if isinstance(limit_risiko, (int, float)):
                formatted = f"Rp {limit_risiko:,.0f}".replace(",", ".")
                st.success(f"💰 **Total Limit Risiko:** {formatted}")
            else:
                st.write(limit_risiko)
        else:
            st.info("ℹ️ Data Limit Risiko belum tersedia.")
            
    # === Tampilkan kembali data residual yang sudah tersimpan (jika ada) ===
    for label, key in {
        "📄 Residual Dampak": "copy_tabel_residual_dampak",
        "📄 Residual Probabilitas": "copy_tabel_residual_probabilitas",
        "📄 Residual Eksposur": "copy_tabel_residual_eksposur"
    }.items():
        if key in st.session_state:
            st.subheader(label)
            st.dataframe(st.session_state[key], use_container_width=True)

    # ✅ Validasi kelengkapan data
    if risiko_q is not None and risiko_k is not None and df_gabungan is not None:
        st.success("✅ Data sudah lengkap. Silakan lanjutkan proses.")
    else:
        st.warning("⚠️ Data belum lengkap. Harap lengkapi Risiko Kuantitatif dan Kualitatif terlebih dahulu.")


    if df_gabungan is not None:
        if df_gabungan is not None:
            with st.expander("📐 Tabel Residual Probabilitas (silahkan edit dan lihat hasil)", expanded=True):
                st.subheader("✏️ Edit Nilai Probabilitas")

                df_residual_prob = buat_tabel_residual_probabilitas(df_gabungan)

                nilai_cols = [col for col in df_residual_prob.columns if col.startswith("Nilai Q")]

                edited_nilai = st.data_editor(
                    df_residual_prob[["Nomor", "Kode Risiko", "Peristiwa Risiko"] + nilai_cols],
                    use_container_width=True,
                    num_rows="dynamic",
                    key="edit_probabilitas_nilai"
                )

                if st.button("🔢 Hitung Skala Otomatis", key="btn_hitung_skala_prob"):
                    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                        col_nilai = f"Nilai {q}"
                        col_skala = f"Skala {q}"
                        if col_nilai in edited_nilai.columns:
                            df_residual_prob[col_nilai] = edited_nilai[col_nilai]
                            df_residual_prob[col_skala] = df_residual_prob[col_nilai].apply(hitung_skala_probabilitas)

                    st.session_state["copy_tabel_residual_probabilitas"] = df_residual_prob
                    st.success("✅ Skala berhasil dihitung ulang berdasarkan nilai probabilitas.")

                st.markdown("### 📄 Hasil Residual Probabilitas Lengkap")
                st.dataframe(df_residual_prob, use_container_width=True)


            with st.expander("💥 Tabel Residual Dampak (silahkan edit & hitung ulang)", expanded=True):
                st.subheader("📝 Input dan Edit Persentase Q1–Q4")

                df_residual_dampak = buat_tabel_residual_dari_gabungan(df_gabungan)
                limit_risiko = st.session_state.get("copy_limit_risiko", 1)

                # Siapkan kolom input persen
                for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                    kol_persen = f"Nilai {q} (%)"
                    nilai_q = df_residual_dampak[f"Nilai {q}"]
                    df_residual_dampak[kol_persen] = (nilai_q / df_residual_dampak["Nilai Dampak"] * 100).round(2)

                # Kolom editor yang bisa diubah user
                kolom_edit = [
                    "Nomor", "Kode Risiko", "Peristiwa Risiko",
                    "Nilai Dampak"
                ] + [f"Nilai {q} (%)" for q in ['Q1', 'Q2', 'Q3', 'Q4']]

                edited_dampak = st.data_editor(
                    df_residual_dampak[kolom_edit],
                    use_container_width=True,
                    num_rows="dynamic",
                    key="edit_dampak_input_persen"
                )

                if st.button("🔢 Hitung Nilai Absolut & Skala Dampak"):
                    for idx, row in edited_dampak.iterrows():
                        nilai_dampak = row["Nilai Dampak"]
                        for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                            kol_persen = f"Nilai {q} (%)"
                            kol_nilai = f"Nilai {q}"
                            kol_skala = f"Skala {q}"

                            persen = row[kol_persen]
                            if pd.notna(persen) and pd.notna(nilai_dampak):
                                nilai_q = (persen / 100) * nilai_dampak
                            else:
                                nilai_q = 0

                            df_residual_dampak.at[idx, kol_nilai] = nilai_q
                            df_residual_dampak.at[idx, kol_skala] = hitung_skala_dampak(nilai_q, limit_risiko)

                    st.session_state["copy_tabel_residual_dampak"] = df_residual_dampak
                    st.success("✅ Nilai Absolut dan Skala Dampak berhasil dihitung.")

                    st.subheader("📄 Hasil Perhitungan Residual Dampak")
                    st.dataframe(df_residual_dampak, use_container_width=True)


            st.subheader("📊 Tabel Eksposur Risiko & Level Risiko (Auto)")

            # Perhitungan otomatis dari 2 tabel residual
            df_level = buat_tabel_eksposur_risiko(df_residual_dampak, df_residual_prob, df_gabungan)

            # Simpan ke session
            st.session_state["copy_tabel_residual_eksposur"] = df_level

            # Tampilkan tabel hasil (tanpa edit)
            with st.expander("📄 Tabel Eksposur Risiko Lengkap", expanded=True):
                st.dataframe(df_level, use_container_width=True)

            # Hitung dan tampilkan total Q4
            total_q4_dict = {}
            if 'Dampak Anggaran' in df_level.columns and 'Nilai Q4' in df_level.columns:
                df_level['Nilai Q4'] = pd.to_numeric(df_level['Nilai Q4'], errors='coerce')

                total_per_kategori = (
                    df_level
                    .groupby('Dampak Anggaran')['Nilai Q4']
                    .sum()
                    .reset_index()
                    .rename(columns={'Nilai Q4': 'Total Nilai Q4'})
                )

                total_q4_dict = dict(zip(total_per_kategori['Dampak Anggaran'], total_per_kategori['Total Nilai Q4']))

                st.subheader("🔢 Dampak Residual Risiko Q4 ")
                for kategori, total in total_q4_dict.items():
                    formatted_total = f"Rp {total:,.2f}".replace(",", ".")
                    st.markdown(f"- **{kategori}:** {formatted_total}")

                total_semua = df_level['Nilai Q4'].sum()
                formatted_total_semua = f"Rp {total_semua:,.2f}".replace(",", ".")
                st.markdown(f"\n**🧮 Total Seluruh Nilai Q4:** {formatted_total_semua}")

            # Simpan juga total ke session state
            st.session_state["copy_residual_biaya"] = total_q4_dict.get("Biaya", 0.0)
            st.session_state["copy_residual_pendapatan"] = total_q4_dict.get("Pendapatan", 0.0)


        # Tombol Update ke Session State
        if df_residual_prob.empty or df_residual_dampak.empty or df_level.empty:
            st.warning("⚠️ Tidak semua tabel residual berhasil dihitung. Pastikan data gabungan, limit risiko, dan format 'Nilai Probabilitas' serta 'Nilai Dampak' sudah benar sebelum melanjutkan.")
        else:
            # Tombol Update ke Session State
            if st.button("🔄 Update Data"):
                st.session_state["copy_tabel_residual_dampak"] = df_residual_dampak
                st.session_state["copy_tabel_residual_probabilitas"] = df_residual_prob
                st.session_state["copy_tabel_residual_eksposur"] = df_level
                st.session_state["copy_residual_biaya"] = total_q4_dict.get("Biaya", 0.0)
                st.session_state["copy_residual_pendapatan"] = total_q4_dict.get("Pendapatan", 0.0)
                st.success("✅ Semua tabel residual & total Q4 (Biaya & Pendapatan) disalin ke session state!")

                        
        # Tombol Simpan ke File Excel
        save_and_download_residual_risk()


def main():
    tampilkan_tabel()

if __name__ == "__main__":
    main()
