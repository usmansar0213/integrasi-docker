import streamlit as st
import pandas as pd
import re
from streamlit.column_config import TextColumn, NumberColumn
import time
import os
from datetime import datetime
import io

# Label Konstanta
BTN_SAVE_LABEL = "💾 Simpan Data ke Excel"
BTN_GET_AI_LABEL = "🤖 Dapatkan Saran AI"
BTN_LOAD_LABEL = "📂 Muat Data dari File"


# Inisialisasi session state
def init_session_state():
    default_values = {
        'copy_metrix_strategi_risiko': pd.DataFrame(columns=["Kode Risiko", "Peristiwa Risiko", "Satuan Ukuran", "Nilai Batasan/Limit"]),
        'copy_deskripsi_risiko': pd.DataFrame(columns=["Kode Risiko", "Peristiwa Risiko", "Deskripsi Peristiwa Risiko", "No. Penyebab Risiko", "Kode Penyebab Risiko", "Penyebab Risiko"]),
        'copy_tabel_gabungan': pd.DataFrame(columns=["Kode Risiko", "Limit Risiko", "Peristiwa Risiko"]),
        'copy_perhitungan_risiko': pd.DataFrame(columns=["Kode Risiko", "Limit Risiko", "Peristiwa Risiko", "Penjelasan Dampak", "Nilai Dampak", "Skala Dampak", "Nilai Probabilitas", "Skala Probabilitas", "Nilai Eksposur Risiko", "Skala Risiko", "Level Nilai Risiko", "Jenis Dampak"]),
        'copy_control_dampak': pd.DataFrame(columns=["Kode Risiko", "Jenis Existing Control", "Existing Control", "Penilaian Efektivitas Kontrol", "Kategori Dampak", "Deskripsi Dampak", "Perkiraan Waktu Terpapar Risiko"]),
        'copy_limit_risiko': "Belum Ditentukan",
        'copy_risiko_kuantitatif': pd.DataFrame(),     # gunakan lowercase dan konsisten
        'copy_risiko_kualitatif': pd.DataFrame()
    }
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value
def cek_data_wajib_awal():
    missing_info = []

    # Cek tabel strategi risiko
    df_strategi = st.session_state.get("copy_metrix_strategi_risiko", pd.DataFrame())
    if df_strategi.empty or "Kode Risiko" not in df_strategi.columns:
        missing_info.append("✅ Tabel Strategi Risiko belum lengkap (minimal kolom 'Kode Risiko').")

    # Cek tabel deskripsi risiko
    df_deskripsi = st.session_state.get("copy_deskripsi_risiko", pd.DataFrame())
    if df_deskripsi.empty or "Kode Risiko" not in df_deskripsi.columns or "Peristiwa Risiko" not in df_deskripsi.columns:
        missing_info.append("✅ Tabel Deskripsi Risiko belum lengkap (minimal kolom 'Kode Risiko' dan 'Peristiwa Risiko').")

    # Cek tabel control dampak
    df_control = st.session_state.get("copy_control_dampak", pd.DataFrame())
    if df_control.empty or "Kode Risiko" not in df_control.columns:
        missing_info.append("⚠️ Tabel Control Dampak kosong atau belum punya kolom 'Kode Risiko'.")


# Tambahan fungsi untuk memastikan data hasil update tetap tersedia saat pindah modul

def persist_updated_data():
    if "temp_risiko_kuantitatif" in st.session_state:
        st.session_state["copy_risiko_kuantitatif"] = st.session_state["temp_risiko_kuantitatif"].copy()

    if "temp_risiko_kualitatif" in st.session_state:
        st.session_state["copy_risiko_kualitatif"] = st.session_state["temp_risiko_kualitatif"].copy()

def merge_tables():
    df_metrix = st.session_state.get('copy_metrix_strategi_risiko', pd.DataFrame()).copy()
    df_deskripsi = st.session_state.get('copy_deskripsi_risiko', pd.DataFrame()).copy()
    df_control = st.session_state.get('copy_control_dampak', pd.DataFrame()).copy()
    df_limit_raw = st.session_state.get("copy_limit_risiko", None)

    # Tangani kemungkinan kesalahan tipe data
    if isinstance(df_limit_raw, pd.DataFrame):
        df_limit = df_limit_raw.copy()
    else:
        # Jika bukan DataFrame, beri peringatan ramah pengguna
        st.warning(
            "⚠️ Data Limit Risiko belum tersedia dalam format yang tepat. "
            "Pastikan Anda telah mengunggah file strategi risiko dengan sheet **'Copy Limit Risiko'** yang sesuai."
        )
        # Tetapkan limit global default sebagai string atau angka
        df_limit = df_limit_raw  # tetap digunakan sebagai angka/string di bagian selanjutnya


    if "Kode Risiko" not in df_metrix.columns or "Kode Risiko" not in df_deskripsi.columns:
        st.error("❌ Kolom 'Kode Risiko' harus ada di tabel strategi dan deskripsi.")
        return pd.DataFrame()

    if "Sikap Terhadap Risiko" not in df_metrix.columns:
        df_metrix["Sikap Terhadap Risiko"] = "Belum Ditentukan"

    # Gabungkan strategi + deskripsi
    merged_df = pd.merge(
        df_metrix,
        df_deskripsi[["Kode Risiko", "Peristiwa Risiko"]],
        on="Kode Risiko",
        how="outer"
    )

    # --- 🔥 Modifikasi bagian Limit Risiko ---
    if isinstance(df_limit, pd.DataFrame) and "Kode Risiko" in df_limit.columns and "Limit Risiko" in df_limit.columns:
        # Kalau copy_limit_risiko berbentuk tabel, lakukan merge per risiko
        merged_df = pd.merge(
            merged_df,
            df_limit[["Kode Risiko", "Limit Risiko"]],
            on="Kode Risiko",
            how="left",
            suffixes=('', '_dari_limit')
        )
        # Bersihkan angka
        merged_df["Limit Risiko"] = merged_df["Limit Risiko"].fillna(0)
        merged_df["Limit Risiko"] = merged_df["Limit Risiko"].astype(str).apply(lambda x: re.sub(r"[^\d]", "", x))
        merged_df["Limit Risiko"] = pd.to_numeric(merged_df["Limit Risiko"], errors="coerce").fillna(0.0)
    else:
        # Kalau copy_limit_risiko hanya 1 angka global
        limit_global = 0
        try:
            limit_global = float(re.sub(r"[^\d]", "", str(df_limit)))
        except:
            limit_global = 0.0
        merged_df["Limit Risiko"] = limit_global

    merged_df.fillna("-", inplace=True)

    # --- Lanjutkan proses seperti biasa ---
    if not df_control.empty and "Kode Risiko" in df_control.columns:
        kolom_control = ["Kode Risiko"]
        for kolom in ["Kategori Dampak", "Deskripsi Dampak", "Dampak Anggaran"]:
            if kolom in df_control.columns:
                kolom_control.append(kolom)
            else:
                st.warning(f"⚠️ Kolom '{kolom}' tidak ditemukan di tabel Control Dampak.")

        df_control_trimmed = df_control[kolom_control].drop_duplicates(subset=["Kode Risiko"])
        merged_df = pd.merge(merged_df, df_control_trimmed, on="Kode Risiko", how="left")

    # Default kolom kalau belum ada
    if "Kategori Dampak" not in merged_df.columns:
        merged_df["Kategori Dampak"] = "Kualitatif"

    if "Deskripsi Dampak" not in merged_df.columns:
        merged_df["Deskripsi Dampak"] = "-"

    if "Dampak Anggaran" not in merged_df.columns:
        merged_df["Dampak Anggaran"] = "Tidak Diketahui"

    # Perhitungan nilai & skala dampak
    def hitung_nilai_dampak(row):
        limit = row["Limit Risiko"]
        kategori_dampak = str(row.get("Kategori Dampak", "")).strip().lower()
        sikap = str(row.get("Sikap Terhadap Risiko", "")).strip().lower()

        if "kuantitatif" in kategori_dampak:
            # 🔥 Untuk Kuantitatif: pakai sikap
            if "strategis" in sikap:
                return 0.6 * limit
            elif "moderat" in sikap:
                return 0.5 * limit
            elif "konservatif" in sikap:
                return 0.3 * limit
            elif "tidak toleran" in sikap:
                return 0.01 * limit
            else:
                return 0
        else:
            # 🔥 Untuk Kualitatif: 1% dari limit
            return 0.01 * limit


    merged_df["Nilai Dampak"] = merged_df.apply(hitung_nilai_dampak, axis=1)

    def hitung_skala_dampak(row):
        limit = row["Limit Risiko"]
        dampak = row["Nilai Dampak"]
        if limit == 0:
            return 0
        persen = (dampak / limit) * 100
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

    merged_df["Skala Dampak"] = merged_df.apply(hitung_skala_dampak, axis=1)

    # Default Probabilitas
    merged_df["Skala Probabilitas"] = 3
    merged_df["Nilai Probabilitas"] = "50%"
    merged_df["Nilai Eksposur Risiko"] = merged_df["Nilai Dampak"] * 0.5

    # Mapping Level Risiko
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

    skala_risiko = []
    level_risiko = []
    for _, row in merged_df.iterrows():
        key = (int(row["Skala Probabilitas"]), int(row["Skala Dampak"]))
        hasil = mapping_level_risiko.get(key, (0, "Tidak Diketahui"))
        skala_risiko.append(hasil[0])
        level_risiko.append(hasil[1])

    merged_df["Skala Risiko"] = skala_risiko
    merged_df["Level Nilai Risiko"] = level_risiko

    merged_df.drop_duplicates(subset=["Kode Risiko", "Peristiwa Risiko"], inplace=True)

    # Simpan ke session_state
    st.session_state["copy_tabel_gabungan"] = merged_df

    return merged_df


def perhitungan_risiko():
    kolom_target = [
        "Kode Risiko", "Kategori Risiko T2 & T3 KBUMN", "Kategori Dampak", "Peristiwa Risiko", 
        "Peristiwa Risiko dari Deskripsi", "Asumsi Perhitungan Dampak", "Nilai Dampak", 
        "Skala Dampak BUMN", "Skala Dampak KBUMN", "Nilai Probabilitas", 
        "Skala Probabilitas BUMN", "Skala Probabilitas KBUMN", "Eksposur Risiko", 
        "Skala Risiko BUMN", "Skala Risiko KBUMN", "Level Risiko BUMN", 
        "Level Risiko KBUMN", "Dampak Anggaran"
    ]

    df_gabungan = st.session_state.get("copy_tabel_gabungan", pd.DataFrame())
    df_final = pd.DataFrame(columns=kolom_target)

    if not df_gabungan.empty:
        df_final["Kode Risiko"] = df_gabungan.get("Kode Risiko", "")
        df_final["Kategori Risiko T2 & T3 KBUMN"] = df_gabungan.get("Kategori Risiko T2 & T3 KBUMN", "")
        df_final["Kategori Dampak"] = df_gabungan.get("Kategori Dampak", "")
        df_final["Peristiwa Risiko"] = df_gabungan.get("Peristiwa Risiko", "")
        df_final["Peristiwa Risiko dari Deskripsi"] = df_gabungan.get("Peristiwa Risiko", "")
        df_final["Asumsi Perhitungan Dampak"] = df_gabungan.get("Deskripsi Dampak", "")
        df_final["Nilai Dampak"] = df_gabungan.get("Nilai Dampak", "")
        df_final["Skala Dampak BUMN"] = df_gabungan.get("Skala Dampak", "")
        df_final["Skala Dampak KBUMN"] = ""
        df_final["Nilai Probabilitas"] = df_gabungan.get("Nilai Probabilitas", "")
        df_final["Skala Probabilitas BUMN"] = df_gabungan.get("Skala Probabilitas", "")
        df_final["Skala Probabilitas KBUMN"] = ""
        df_final["Eksposur Risiko"] = df_gabungan.get("Nilai Eksposur Risiko", "")
        df_final["Skala Risiko BUMN"] = df_gabungan.get("Skala Risiko", "")
        df_final["Skala Risiko KBUMN"] = ""
        df_final["Level Risiko BUMN"] = df_gabungan.get("Level Nilai Risiko", "")
        df_final["Level Risiko KBUMN"] = ""
        df_final["Dampak Anggaran"] = df_gabungan.get("Dampak Anggaran", "")

        # Klasifikasikan Kategori Dampak menjadi Kuantitatif / Kualitatif
        def klasifikasi_kategori(k):
            if isinstance(k, str) and "kuantitatif" in k.lower():
                return "Kuantitatif"
            else:
                return "Kualitatif"
        
        df_final["Kategori Dampak"] = df_final["Kategori Dampak"].apply(klasifikasi_kategori)

        # Simpan ke session state sesuai kategorinya
        st.session_state["copy_Risiko_Kuantitatif"] = df_final[df_final["Kategori Dampak"] == "Kuantitatif"].reset_index(drop=True)
        st.session_state["copy_Risiko_Kualitatif"] = df_final[df_final["Kategori Dampak"] == "Kualitatif"].reset_index(drop=True)
def tampilkan_editor_risiko():
    def hitung_eksposur_dan_level(df):
        if df.empty:
            return df

        # Hitung skala probabilitas
        def skala_prob(p):
            try:
                p = float(str(p).replace('%', '').strip())
                if p <= 1:
                    p *= 100
            except:
                p = 0
            if p <= 10:
                return 1
            elif p <= 30:
                return 2
            elif p <= 50:
                return 3
            elif p <= 70:
                return 4
            else:
                return 5

        # Hitung skala dampak
        def skala_dampak(d):
            try:
                d = float(d)
            except:
                d = 0
            if d <= 20:
                return 1
            elif d <= 40:
                return 2
            elif d <= 60:
                return 3
            elif d <= 80:
                return 4
            else:
                return 5

        # Mapping level risiko
        mapping_level = {
            (1, 1): (1, "Hijau Tua"), (2, 1): (2, "Hijau Tua"), (3, 1): (3, "Hijau Tua"),
            (4, 1): (4, "Hijau Tua"), (5, 1): (7, "Hijau Muda"), (1, 2): (5, "Hijau Tua"),
            (2, 2): (6, "Hijau Muda"), (3, 2): (8, "Hijau Muda"), (4, 2): (9, "Hijau Muda"),
            (5, 2): (12, "Kuning"), (1, 3): (10, "Hijau Muda"), (2, 3): (11, "Hijau Muda"),
            (3, 3): (13, "Kuning"), (4, 3): (14, "Kuning"), (5, 3): (17, "Oranye"),
            (1, 4): (15, "Kuning"), (2, 4): (16, "Oranye"), (3, 4): (18, "Oranye"),
            (4, 4): (19, "Oranye"), (5, 4): (22, "Merah"), (1, 5): (20, "Merah"),
            (2, 5): (21, "Merah"), (3, 5): (23, "Merah"), (4, 5): (24, "Merah"), (5, 5): (25, "Merah"),
        }

        df["Skala Probabilitas BUMN"] = df["Nilai Probabilitas"].apply(skala_prob)
        df["Skala Dampak BUMN"] = df["Nilai Dampak"].apply(skala_dampak)

        df["Eksposur Risiko"] = df["Nilai Dampak"] * (df["Skala Probabilitas BUMN"] / 5)

        skala_risiko = []
        level_risiko = []
        for _, row in df.iterrows():
            key = (row["Skala Probabilitas BUMN"], row["Skala Dampak BUMN"])
            hasil = mapping_level.get((key), (0, "Tidak Diketahui"))
            skala_risiko.append(hasil[0])
            level_risiko.append(hasil[1])

        df["Skala Risiko BUMN"] = skala_risiko
        df["Level Risiko BUMN"] = level_risiko

        df["Skala Risiko KBUMN"] = df["Skala Risiko BUMN"]
        df["Level Risiko KBUMN"] = df["Level Risiko BUMN"]

        return df

    for jenis in ["kuantitatif", "kualitatif"]:
        df_asli = st.session_state.get(f"copy_risiko_{jenis}", pd.DataFrame()).copy()
        if df_asli.empty:
            continue

        st.subheader(f"✏️ Editor Risiko Inheren {jenis.capitalize()}")
        df_edit = df_asli[["Kode Risiko", "Peristiwa Risiko", "Nilai Dampak", "Nilai Probabilitas"]].copy()
        df_edit.insert(0, "Nomor", range(1, len(df_edit)+1))

        edited_df = st.data_editor(
            df_edit,
            num_rows="fixed",
            use_container_width=True,
            key=f"editor_only_{jenis}",
            column_config={
                "Nilai Dampak": NumberColumn(step=1.0),
                "Nilai Probabilitas": TextColumn(help="Boleh dalam persen (misal '40%')")
            },
            hide_index=True
        )

        if st.button(f"🔁 Recalculate {jenis.capitalize()}", key=f"btn_recalc_{jenis}"):
            df_recalc = df_asli.copy()
            for idx in edited_df.index:
                kode = edited_df.at[idx, "Kode Risiko"]
                dampak_baru = edited_df.at[idx, "Nilai Dampak"]
                prob_baru = edited_df.at[idx, "Nilai Probabilitas"]
                df_recalc.loc[df_recalc["Kode Risiko"] == kode, "Nilai Dampak"] = dampak_baru
                df_recalc.loc[df_recalc["Kode Risiko"] == kode, "Nilai Probabilitas"] = prob_baru

            df_final = hitung_eksposur_dan_level(df_recalc)

            st.session_state[f"hasil_recalc_{jenis}"] = df_final
            st.session_state[f"copy_risiko_{jenis}"] = df_final
            st.success(f"✅ Hasil risiko {jenis} berhasil dihitung ulang.")

        if st.session_state.get(f"hasil_recalc_{jenis}") is not None:
            st.subheader(f"📊 Hasil Risiko Inheren {jenis.capitalize()}")
            st.dataframe(st.session_state[f"hasil_recalc_{jenis}"], use_container_width=True)


def update_data_editor():
    # Ambil hasil editan terbaru dari session_state
    df_kuantitatif = st.session_state.get("copy_risiko_kuantitatif", pd.DataFrame()).copy()
    df_kualitatif = st.session_state.get("copy_risiko_kualitatif", pd.DataFrame()).copy()

    # Tambahkan kolom nomor
    def tambahkan_nomor(df):
        if "Nomor" in df.columns:
            df = df.drop(columns=["Nomor"])
        df.insert(0, "Nomor", range(1, len(df) + 1))
        return df

    # Fungsi hitung ulang eksposur
    def hitung_eksposur_dan_level(df):
        if df.empty:
            return df

        # Hitung Eksposur Risiko
        df["Prob (%)"] = df["Nilai Probabilitas"].astype(str).str.replace('%', '').astype(float) / 100
        df["Eksposur Risiko"] = df["Nilai Dampak"] * df["Prob (%)"]
        df.drop(columns=["Prob (%)"], inplace=True)

        # Hitung Skala Risiko BUMN dan Level Risiko BUMN
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

        skala_bumn = []
        level_bumn = []
        for _, row in df.iterrows():
            skala_prob = int(row.get("Skala Probabilitas BUMN", 0))
            skala_dampak = int(row.get("Skala Dampak BUMN", 0))
            hasil = mapping_level_risiko.get((skala_prob, skala_dampak), (0, "Tidak Diketahui"))
            skala_bumn.append(hasil[0])
            level_bumn.append(hasil[1])

        df["Skala Risiko BUMN"] = skala_bumn
        df["Level Risiko BUMN"] = level_bumn

        return df


    # Proses update
    df_kuantitatif = hitung_eksposur_dan_level(df_kuantitatif)
    df_kualitatif = hitung_eksposur_dan_level(df_kualitatif)


    df_kualitatif = tambahkan_nomor(df_kualitatif)

    # Simpan hasil final ke session_state
    st.session_state["copy_Tabel_Kuantitatif"] = df_kuantitatif.copy()
    st.session_state["copy_Tabel_Kualitatif"] = df_kualitatif.copy()

    st.success("✅ Data editor berhasil diperbarui dan Eksposur Risiko sudah dihitung ulang.")
import io
import os
from datetime import datetime
import pandas as pd
import streamlit as st

def save_and_download_inherent_dampak(daftar_tabel, kode_perusahaan="NA"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # 📁 Buat folder penyimpanan lokal jika belum ada
    folder_path = "C:/saved"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Path untuk penyimpanan lokal
    server_file_path = os.path.join(folder_path, f"Inherent_Dampak_{timestamp}.xlsx")

    # 🎯 Buffer untuk download di Streamlit
    output = io.BytesIO()

    # 💾 Simpan ke 2 tempat: server & buffer download
    with pd.ExcelWriter(server_file_path, engine='xlsxwriter') as writer_server, \
         pd.ExcelWriter(output, engine='xlsxwriter') as writer_download:

        for tabel in daftar_tabel:
            df_to_save = st.session_state.get(f"copy_{tabel}", pd.DataFrame())
            if isinstance(df_to_save, pd.DataFrame) and not df_to_save.empty:
                df_save = df_to_save.copy()

                # Bersihkan kolom Nomor dulu jika ada
                if "Nomor" in df_save.columns:
                    df_save = df_save.drop(columns=["Nomor"])

                # Tambahkan kembali kolom Nomor di awal
                df_save.insert(0, "Nomor", range(1, len(df_save) + 1))

                sheet_name = tabel.replace("_", " ").title()[:31]

                # Simpan ke dua tempat
                df_save.to_excel(writer_server, sheet_name=sheet_name, index=False)
                df_save.to_excel(writer_download, sheet_name=sheet_name, index=False)

    output.seek(0)  # reset buffer

    # ✅ Tampilkan info sukses
    st.success(f"✅ Data berhasil disimpan ke server: `{server_file_path}`")

    # ⬇️ Tampilkan tombol unduh
    st.download_button(
        label="⬇️ Unduh Data Risiko Inherent",
        data=output,
        file_name=f"Inherent_Dampak_{timestamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def load_uploaded_file(uploaded_file):
    """Muat file upload untuk Risiko Inherent, Strategi, Sasaran, atau Profil Risiko."""
    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = [sheet.lower().strip() for sheet in xls.sheet_names]

            # Deteksi jika ini file hasil ekspor 'Inherent_Dampak_'
            if all(any(kata in sheet for kata in ['kuantitatif', 'kualitatif']) for sheet in sheet_names):
                st.info("📄 Deteksi: File hasil ekspor risiko inherent.")
                for sheet in xls.sheet_names:
                    df = xls.parse(sheet)
                    sheet_lc = sheet.lower().replace(" ", "_")

                    st.session_state[f"copy_{sheet_lc}"] = df

                    if "Nomor" not in df.columns:
                        df.insert(0, "Nomor", range(1, len(df) + 1))

                    tipe = sheet_lc.split('_')[-1]
                    st.session_state[f"temp_risiko_{tipe}"] = df
                    st.session_state[f"copy_risiko_{tipe}"] = df
                    st.session_state[f"copy_Tabel_{tipe.capitalize()}"] = df

                    st.success(f"✅ Sheet '{sheet}' dimuat ke editor '{sheet_lc}'.")

                st.session_state["file_uploaded"] = True
                return  # selesai jika file inherent

            # === File Strategi Risiko ===
            if any('metrix' in s or 'ambang' in s or 'limit' in s for s in sheet_names):
                df_metrix = pd.read_excel(xls, sheet_name="Copy Metrix Strategi Risiko")
                df_limit = pd.read_excel(xls, sheet_name="Copy Limit Risiko")
                df_ambang = pd.read_excel(xls, sheet_name="Copy Ambang Batas Risiko")

                st.session_state["copy_metrix_strategi_risiko"] = df_metrix
                st.session_state["copy_limit_risiko"] = df_limit
                st.session_state["copy_ambang_batas_risiko"] = df_ambang
                st.session_state["tipe_file"] = "strategi_risiko"
                st.success("✅ File Strategi Risiko berhasil dimuat.")
                st.session_state["file_uploaded"] = True
                return

            # === File Sasaran Strategi Bisnis ===
            if any('sasaran' in s for s in sheet_names):
                df_sasaran = pd.read_excel(xls, sheet_name="sasaran_strategi_bisnis")
                st.session_state["copy_sasaran_strategi_bisnis"] = df_sasaran
                st.session_state["tipe_file"] = "sasaran_strategi_bisnis"
                st.success("✅ File Sasaran Strategi Bisnis berhasil dimuat.")
                st.session_state["file_uploaded"] = True
                return

            # === File Profil Risiko ===
            if any('deskripsi' in s or 'control' in s or 'key risk indicator' in s for s in sheet_names):
                df_deskripsi = pd.read_excel(xls, sheet_name="deskripsi_risiko")
                df_control = pd.read_excel(xls, sheet_name="control_dampak")
                df_kri = pd.read_excel(xls, sheet_name="key_risk_indicator")

                st.session_state["copy_deskripsi_risiko"] = df_deskripsi
                st.session_state["copy_control_dampak"] = df_control
                st.session_state["copy_key_risk_indicator"] = df_kri
                st.session_state["tipe_file"] = "profil_risiko"
                st.success("✅ File Profil Risiko berhasil dimuat.")
                st.session_state["file_uploaded"] = True
                return

            st.warning("⚠️ Tidak dapat mengenali isi file. Pastikan format sheet sesuai yang diharapkan.")

        except Exception as e:
            st.error(f"❌ Gagal memuat file Excel: {e}")

def cek_dan_total_eksposur():
    total_kuantitatif = 0
    total_kualitatif = 0

    # 🔥 Gunakan hasil RECALCULATE
    df_kuant = st.session_state.get("copy_Tabel_Kuantitatif", pd.DataFrame()).copy()
    df_kual = st.session_state.get("copy_Tabel_Kualitatif", pd.DataFrame()).copy()

    if not df_kuant.empty:
        df_kuant["Prob (%)"] = df_kuant["Nilai Probabilitas"].apply(
            lambda x: float(str(x).replace('%', '').strip()) if float(str(x).replace('%', '').strip()) > 1 else float(str(x).replace('%', '').strip()) * 100
        ) / 100
        df_kuant["Eksposur Hitung Ulang"] = df_kuant["Nilai Dampak"] * df_kuant["Prob (%)"]
        df_kuant["Cocok?"] = df_kuant["Eksposur Risiko"].round(2) == df_kuant["Eksposur Hitung Ulang"].round(2)
        if not df_kuant["Cocok?"].all():
            st.warning("⚠️ Ada ketidaksesuaian perhitungan Eksposur Risiko Kuantitatif.")
        total_kuantitatif = df_kuant["Eksposur Hitung Ulang"].sum()

    if not df_kual.empty:
        df_kual["Prob (%)"] = df_kual["Nilai Probabilitas"].apply(
            lambda x: float(str(x).replace('%', '').strip()) if float(str(x).replace('%', '').strip()) > 1 else float(str(x).replace('%', '').strip()) * 100
        ) / 100
        df_kual["Eksposur Hitung Ulang"] = df_kual["Nilai Dampak"] * df_kual["Prob (%)"]
        df_kual["Cocok?"] = df_kual["Eksposur Risiko"].round(2) == df_kual["Eksposur Hitung Ulang"].round(2)
        if not df_kual["Cocok?"].all():
            st.warning("⚠️ Ada ketidaksesuaian perhitungan Eksposur Risiko Kualitatif.")
        total_kualitatif = df_kual["Eksposur Hitung Ulang"].sum()

    combined_df = pd.concat([df_kuant, df_kual], ignore_index=True)

    total_ekposur_pendapatan = 0
    total_ekposur_biaya = 0
    total_ekposur_tak_terklasifikasi = 0

    if not combined_df.empty and "Dampak Anggaran" in combined_df.columns:
        # Normalisasi kolom
        combined_df["Dampak Anggaran"] = (
            combined_df["Dampak Anggaran"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        # Hanya ambil kategori valid
        combined_df["Dampak Anggaran"] = combined_df["Dampak Anggaran"].apply(lambda x: 
            "Pendapatan" if "pendapatan" in x else 
            "Biaya" if "biaya" in x else "Tak Terklasifikasi"
        )


        total_ekposur_pendapatan = combined_df[combined_df["Dampak Anggaran"] == "Pendapatan"]["Eksposur Hitung Ulang"].sum()
        total_ekposur_biaya = combined_df[combined_df["Dampak Anggaran"] == "Biaya"]["Eksposur Hitung Ulang"].sum()
        total_ekposur_tak_terklasifikasi = combined_df[
            ~combined_df["Dampak Anggaran"].isin(["Pendapatan", "Biaya"])
        ]["Eksposur Hitung Ulang"].sum()

    total_seluruh = total_kuantitatif + total_kualitatif

    # Simpan ke session_state
    st.session_state["temp_total_ekposur"] = total_seluruh
    st.session_state["copy_total_eksposur_pendapatan"] = total_ekposur_pendapatan
    st.session_state["copy_total_eksposur_biaya"] = total_ekposur_biaya
    st.session_state["copy_total_eksposur_tak_terklasifikasi"] = total_ekposur_tak_terklasifikasi

        # Tampilkan hasil
    st.markdown(f"**📊 Total Eksposur Risiko Kuantitatif:** {total_kuantitatif:,.2f}")
    st.markdown(f"**📊 Total Eksposur Risiko Kualitatif:** {total_kualitatif:,.2f}")

    # Garis pemisah
    st.markdown("---")

    st.markdown(f"**📈 Total Exposure Risiko Berdampak pada Pendapatan:** {total_ekposur_pendapatan:,.2f}")
    st.markdown(f"**📉 Total Exposure Risiko Berdampak pada Biaya:** {total_ekposur_biaya:,.2f}")
    st.markdown(f"**❓ Total Exposure Risiko Tak Terklasifikasi:** {total_ekposur_tak_terklasifikasi:,.2f}")

    # Garis pemisah
    st.markdown("---")

    st.markdown(f"### ✅ **Total Eksposur Keseluruhan Risiko: {total_seluruh:,.2f}**")

    if total_ekposur_tak_terklasifikasi > 0:
        st.warning("⚠️ Terdapat risiko dengan `Dampak Anggaran` yang belum diklasifikasikan sebagai 'Pendapatan' atau 'Biaya'.")

def main():
    init_session_state()
    persist_updated_data()

    st.title("📊 Risiko Inherent")

    cek_data_wajib_awal()

    uploaded_files = st.file_uploader(
    "📥 Silakan unggah **file Strategi Risiko** dan **file Profil Risiko** (.xlsx)",
    type=["xlsx"],
    accept_multiple_files=True,
    key="file_uploader_multi"
    )


    if uploaded_files:
        for uploaded_file in uploaded_files:
            load_uploaded_file(uploaded_file)
            st.session_state["file_uploaded"] = True

    # Lanjutkan hanya jika sudah upload
    if st.session_state.get("file_uploaded", False):
        with st.expander("📂 Data Yang Dimuat", expanded=False):
            st.subheader("📌 Tabel Strategi Risiko")
            st.dataframe(st.session_state.get("copy_metrix_strategi_risiko", pd.DataFrame()), use_container_width=True)

            st.subheader("📌 Tabel Deskripsi Risiko")
            st.dataframe(st.session_state.get("copy_deskripsi_risiko", pd.DataFrame()), use_container_width=True)

            st.subheader("🛡️ Tabel Control Dampak")
            st.dataframe(st.session_state.get("copy_control_dampak", pd.DataFrame()), use_container_width=True)

            st.subheader("🔗 Gabungan Tabel Risiko")
            gabungan = merge_tables()
            st.dataframe(gabungan, use_container_width=True)

        # 🧮 Hitung risiko dan klasifikasikan
        perhitungan_risiko()

        # 🔁 Sinkronkan hasil ke editor & session_state
        if st.session_state.get("copy_Risiko_Kuantitatif", pd.DataFrame()).shape[0] > 0:
            df_k = st.session_state["copy_Risiko_Kuantitatif"].copy()
            st.session_state["copy_risiko_kuantitatif"] = df_k
            if "Nomor" in df_k.columns:
                df_k.drop(columns=["Nomor"], inplace=True)
            df_k.insert(0, "Nomor", range(1, len(df_k) + 1))
            st.session_state["temp_risiko_kuantitatif"] = df_k
            st.session_state["copy_Tabel_Kuantitatif"] = df_k.copy()

        if st.session_state.get("copy_Risiko_Kualitatif", pd.DataFrame()).shape[0] > 0:
            df_kk = st.session_state["copy_Risiko_Kualitatif"].copy()
            st.session_state["copy_risiko_kualitatif"] = df_kk
            if "Nomor" in df_kk.columns:
                df_kk.drop(columns=["Nomor"], inplace=True)
            df_kk.insert(0, "Nomor", range(1, len(df_kk) + 1))
            st.session_state["temp_risiko_kualitatif"] = df_kk
            st.session_state["copy_Tabel_Kualitatif"] = df_kk.copy()

        # ✍️ Tampilkan editor risiko jika data tersedia
        if not st.session_state.get("copy_Tabel_Kuantitatif", pd.DataFrame()).empty or \
           not st.session_state.get("copy_Tabel_Kualitatif", pd.DataFrame()).empty:
            tampilkan_editor_risiko()
            cek_dan_total_eksposur()
        else:
            st.info("ℹ️ Belum ada data risiko untuk ditampilkan. Pastikan file sudah dimuat dan dihitung.")

        # 🔄 Tombol update
        if st.button("🔄 Update"):
            update_data_editor()

            with st.expander("📋 Hasil Perubahan Setelah Update", expanded=False):
                st.subheader("✅ Risiko Kuantitatif (Setelah Update)")
                st.dataframe(st.session_state.get("copy_Tabel_Kuantitatif", pd.DataFrame()), use_container_width=True)

                st.subheader("✅ Risiko Kualitatif (Setelah Update)")
                st.dataframe(st.session_state.get("copy_Tabel_Kualitatif", pd.DataFrame()), use_container_width=True)

            # Simpan dan unduh
            daftar_tabel = ["Tabel_Kuantitatif", "Tabel_Kualitatif"]
            save_and_download_inherent_dampak(daftar_tabel, kode_perusahaan="ABC")
    else:
        st.info("📥 Silakan unggah file terlebih dahulu untuk mulai memproses data risiko inherent.")

if __name__ == "__main__":
    main()
