import streamlit as st
import pandas as pd
import json
import re
import os
from datetime import datetime
import openai
import graphviz  # ✅ PENTING: Tambahkan ini
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import uuid  # pastikan sudah ada di atas jika belum
from modules.utils import get_user_file, get_user_folder
import zipfile
import io


# ======================== KONFIGURASI ========================
NAMA_TABEL = "fault_tree"
FOLDER_SIMPAN = None  # Ditunda hingga session tersedia

# ======================== LOAD ENV & API KEY ========================
openai.api_key = st.secrets["openai_api_key"]

# ======================== INISIALISASI SESSION STATE ========================
def init_session():
    if f"copy_{NAMA_TABEL}" not in st.session_state:
        st.session_state[f"copy_{NAMA_TABEL}"] = pd.DataFrame(columns=[
            "ID", "Nama Event", "Parent ID", "Tipe Hubungan", "Probabilitas"
        ])
    if "top_event" not in st.session_state:
        st.session_state.top_event = ""
    if "deskripsi_event" not in st.session_state:
        st.session_state.deskripsi_event = ""

# ======================== PARSING JSON GPT ========================
def extract_json_from_response(response_text):
    try:
        pattern = re.compile(r'\[.*\]', re.DOTALL)
        match = pattern.search(response_text)
        if match:
            return json.loads(match.group())
        else:
            return None
    except json.JSONDecodeError:
        return None

# ======================== GPT REQUEST ========================
def get_gpt_fault_tree(top_event, deskripsi):
    prompt = f"""
Buatkan Fault Tree Analysis dalam format JSON array untuk top event berikut:
Top Event: {top_event}
Deskripsi: {deskripsi}

Output JSON harus berisi list dict dengan struktur:
"ID", "Nama Event", "Parent ID", "Tipe Hubungan (AND/OR)", dan opsional "Probabilitas" (0-1)
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Kamu adalah analis risiko yang ahli dalam Fault Tree Analysis."},
            {"role": "user", "content": prompt}
        ]
    )
    return extract_json_from_response(response.choices[0].message.content)

# ======================== INPUT TOP EVENT ========================
def input_top_event():
    st.subheader("📌 Masukkan Top Event")
    st.session_state.top_event = st.text_input("Top Event", value=st.session_state.top_event)
    st.session_state.deskripsi_event = st.text_area("Deskripsi Top Event", value=st.session_state.deskripsi_event)
    if st.button("🤖 Buat Struktur FTA dengan GPT"):
        if not st.session_state.top_event:
            st.warning("Masukkan Top Event terlebih dahulu!")
            return
        with st.spinner("Meminta bantuan GPT untuk menyusun struktur..."):
            hasil = get_gpt_fault_tree(st.session_state.top_event, st.session_state.deskripsi_event)
            if hasil:
                st.session_state[f"copy_{NAMA_TABEL}"] = pd.DataFrame(hasil)
                st.success("✅ Struktur berhasil dibuat!")
            else:
                st.error("❌ Gagal memproses respon dari GPT.")

# ======================== TAMPILKAN EDITOR ========================
def tampilkan_editor():
    st.subheader("📋 Struktur Fault Tree Analysis")
    st.markdown("Tabel di bawah ini menunjukkan struktur event dan hubungan logika antar penyebab.")

    with st.expander("📖 Petunjuk Pengisian Tabel"):
        st.markdown("""
        Silakan isi atau sesuaikan data pada tabel berikut sesuai struktur Fault Tree Analysis (FTA) Anda.

        **🔹 Penjelasan Kolom:**
        - **ID**: Nomor unik untuk setiap event. Disarankan angka urut (contoh: 1, 2, 3...).
        - **Nama Event**: Deskripsi singkat dari event atau penyebab (contoh: *Kerusakan Peralatan*).
        - **Parent ID**: Diisi dengan `ID` dari event induk. Kosongkan jika ini adalah *Top Event*.
        - **Tipe Hubungan**:
            - `AND`: Semua anak harus terjadi agar induk terjadi.
            - `OR`: Salah satu anak cukup untuk menyebabkan induk.
        - **Probabilitas**: Nilai antara `0` dan `1` (contoh: `0.2` untuk 20%) yang menunjukkan kemungkinan event terjadi.

        ⚠️ **Catatan Penting:**
        - Pastikan tidak ada **ID ganda**.
        - **Parent ID** harus merujuk pada ID yang valid di tabel.
        - Probabilitas bisa dikosongkan jika belum diketahui, tapi akan dibutuhkan saat perhitungan.
        """)

    df = st.session_state[f"copy_{NAMA_TABEL}"]
    
    # Editor hanya satu kali, key harus tetap!
    edited_df = st.data_editor(df, key="editor_fta", num_rows="dynamic")

    if st.button("💾 Update Struktur Event"):
        st.session_state[f"copy_{NAMA_TABEL}"] = edited_df
        st.success("✅ Struktur event berhasil diperbarui.")
def tampilkan_visualisasi():
    st.subheader("📈 Visualisasi Pohon Kesalahan")
    st.markdown("Diagram di bawah menunjukkan hubungan antar event berdasarkan logika AND/OR.")
    df = st.session_state[f"copy_{NAMA_TABEL}"]

    dot = graphviz.Digraph()
    dot.attr(rankdir="TB")

    for _, row in df.iterrows():
        label = f"{row['ID']}: {row['Nama Event']}\nP={row['Probabilitas']}"
        dot.node(str(row['ID']), label)

    for _, row in df.iterrows():
        parent_id = row['Parent ID']
        if pd.notna(parent_id) and str(parent_id).strip() != '':
            try:
                dot.edge(str(int(float(parent_id))), str(row['ID']), label=row['Tipe Hubungan'])
            except ValueError:
                st.warning(f"⚠️ ID Parent tidak valid: '{parent_id}' pada event '{row['Nama Event']}'")

    st.graphviz_chart(dot)
    return dot  # 🆕 Tambahkan ini

def simpan_visualisasi(dot):
    nama_top_event = st.session_state.get("top_event", "top_event_kosong").strip().replace(" ", "_")
    tanggal = datetime.now().strftime("%d%m%y")
    nama_file = os.path.join(FOLDER_SIMPAN, f"fault_tree_{nama_top_event}_time_{tanggal}")


    try:
        dot.render(filename=nama_file, format="png", cleanup=True)
        st.success(f"🖼️ Visualisasi disimpan sebagai: {nama_file}.png")
    except Exception as e:
        st.error(f"❌ Gagal menyimpan visualisasi: {e}")

        
def generate_dot_only():
    df = st.session_state[f"copy_{NAMA_TABEL}"]
    dot = graphviz.Digraph()
    dot.attr(rankdir="TB")

    for _, row in df.iterrows():
        label = f"{row['ID']}: {row['Nama Event']}\nP={row['Probabilitas']}"
        dot.node(str(row['ID']), label)

    for _, row in df.iterrows():
        parent_id = row['Parent ID']
        if pd.notna(parent_id) and str(parent_id).strip() != '':
            try:
                dot.edge(str(int(float(parent_id))), str(row['ID']), label=row['Tipe Hubungan'])
            except ValueError:
                pass  # Hindari error saat simpan
    return dot

# ======================== HITUNG PROBABILITAS ========================
def hitung_probabilitas():
    st.subheader("📐 Perhitungan Probabilitas Top Event")
    st.markdown("Probabilitas dihitung berdasarkan logika kombinasi AND dan OR dari anak node.")
    df = st.session_state[f"copy_{NAMA_TABEL}"].copy()

    # 🔧 Perbaikan penting
    df["Parent ID"] = df["Parent ID"].replace("", pd.NA)

    df.set_index("ID", inplace=True)

    def kalkulasi_cabang(parent_id):
        anak = df[df["Parent ID"] == parent_id]
        if anak.empty:
            return float(df.at[parent_id, "Probabilitas"])
        tipe = anak["Tipe Hubungan"].iloc[0]
        prob_list = [kalkulasi_cabang(i) for i in anak.index]
        if tipe == "AND":
            return round(pd.Series(prob_list).prod(), 5)
        else:
            return round(1 - pd.Series([(1 - p) for p in prob_list]).prod(), 5)

    try:
        top_event_candidates = df[pd.isna(df["Parent ID"])].index
        if top_event_candidates.empty:
            st.warning("⚠️ Tidak ditemukan top event dengan Parent ID kosong.")
            return
        top_event_id = top_event_candidates[0]
        hasil = kalkulasi_cabang(top_event_id)
        st.success(f"✅ Probabilitas total terjadinya '{df.at[top_event_id, 'Nama Event']}' adalah {hasil}")
    except Exception as e:
        st.error(f"❌ Gagal menghitung probabilitas: {e}")


# ======================== IDENTIFIKASI RISIKO TINGGI ========================
# ======================== IDENTIFIKASI RISIKO TINGGI ========================
def identifikasi_kontributor(threshold=0.4):
    st.subheader("🎯 Kontributor Risiko Tertinggi")
    df = st.session_state[f"copy_{NAMA_TABEL}"].copy()
    df["Probabilitas"] = pd.to_numeric(df["Probabilitas"], errors="coerce").fillna(0.0)
    risiko_tinggi = df[df["Probabilitas"] > threshold]
    st.markdown(f"Menampilkan event dengan probabilitas > {threshold}:")
    st.dataframe(risiko_tinggi)


# ======================== RENCANA MITIGASI ========================
def rencana_mitigasi():
    st.subheader("🛡️ Rencana Mitigasi untuk Event Berisiko Tinggi")
    df = st.session_state[f"copy_{NAMA_TABEL}"].copy()
    df["Probabilitas"] = pd.to_numeric(df["Probabilitas"], errors="coerce").fillna(0.0)

    risiko_tinggi = df[df["Probabilitas"] > 0.4][["ID", "Nama Event", "Probabilitas"]]
    risiko_tinggi = risiko_tinggi.rename(columns={"Nama Event": "Event"})
    risiko_tinggi["Rencana Mitigasi"] = ""

    st.session_state.mitigasi_df = risiko_tinggi.reset_index(drop=True)

    st.data_editor(
        st.session_state.mitigasi_df,
        key="editor_mitigasi",
        num_rows="dynamic",
        use_container_width=True,  # ✅ Melebar secara keseluruhan
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Event": st.column_config.TextColumn("Event", width="medium"),
            "Probabilitas": st.column_config.NumberColumn("Probabilitas", format="%.2f", width="small"),
            "Rencana Mitigasi": st.column_config.TextColumn(
                "Rencana Mitigasi",
                width="stretch"  # ← hint ke Streamlit (tidak error)
            )
        }
    )

# ======================== SIMULASI MITIGASI ========================
def simulasi_mitigasi():
    st.markdown("---")
    st.markdown("### 🔁 Simulasi Probabilitas Setelah Mitigasi")
    st.markdown("Silakan edit probabilitas setiap event setelah mitigasi pada tabel berikut.")

    df = st.session_state[f"copy_{NAMA_TABEL}"].copy()
    df = df[["ID", "Nama Event", "Parent ID", "Probabilitas"]].rename(columns={"Nama Event": "Event"})
    df["Probabilitas"] = pd.to_numeric(df["Probabilitas"], errors="coerce").fillna(0.0)
    df["Parent ID"] = df["Parent ID"].replace(["", "nan"], pd.NA)
    df = df.reset_index(drop=True)
    st.session_state.simulasi_df = df

    edited_df = st.data_editor(df, key="editor_simulasi_" + str(datetime.now().timestamp()), num_rows="dynamic", height=400)

    try:
        df_simulasi = edited_df.copy()
        df_full = st.session_state[f"copy_{NAMA_TABEL}"].copy()
        df_full.set_index("ID", inplace=True)
        for _, row in df_simulasi.iterrows():
            df_full.at[row["ID"], "Probabilitas"] = row["Probabilitas"]

        def kalkulasi(id):
            anak = df_full[df_full["Parent ID"] == id]
            if anak.empty:
                return float(df_full.at[id, "Probabilitas"])
            tipe = anak["Tipe Hubungan"].iloc[0]
            prob_list = [kalkulasi(i) for i in anak.index]
            if tipe == "AND":
                return round(pd.Series(prob_list).prod(), 5)
            else:
                return round(1 - pd.Series([(1 - p) for p in prob_list]).prod(), 5)

        df_full["Parent ID"] = df_full["Parent ID"].replace(["", "nan"], pd.NA)
        top_event_candidates = df_full[pd.isna(df_full["Parent ID"])].index
        if top_event_candidates.empty:
            st.warning("⚠️ Tidak ditemukan top event dengan Parent ID kosong.")
            return
        top_event_id = top_event_candidates[0]
        hasil = kalkulasi(top_event_id)
        st.success(f"🎯 Probabilitas Top Event setelah mitigasi adalah: {hasil}")
    except Exception as e:
        st.error(f"❌ Gagal menghitung simulasi mitigasi: {e}")

def hitung_probabilitas_manual(df):
    try:
        df = df.copy()
        df["Parent ID"] = df["Parent ID"].replace("", pd.NA)
        df.set_index("ID", inplace=True)

        def kalkulasi(id):
            anak = df[df["Parent ID"] == id]
            if anak.empty:
                return float(df.at[id, "Probabilitas"])
            tipe = anak["Tipe Hubungan"].iloc[0]
            prob_list = [kalkulasi(i) for i in anak.index]
            return round(pd.Series(prob_list).prod(), 5) if tipe == "AND" else round(1 - pd.Series([1 - p for p in prob_list]).prod(), 5)

        top_event_id = df[pd.isna(df["Parent ID"])].index[0]
        return kalkulasi(top_event_id)
    except:
        return "Error"


# ======================== SIMPAN FILE ========================
def simpan_ke_excel():
    # Ambil nama top event dan format ke nama file-friendly
    nama_top_event = st.session_state.get("top_event", "top_event_kosong").strip().replace(" ", "_")
    tanggal = datetime.now().strftime("%d%m%y")
    nama_file = os.path.join(FOLDER_SIMPAN, f"fault_tree_{nama_top_event}_time_{tanggal}.xlsx")


    try:
        with pd.ExcelWriter(nama_file, engine='xlsxwriter') as writer:
            workbook = writer.book
            worksheet = workbook.add_worksheet("Rekap FTA")
            writer.sheets["Rekap FTA"] = worksheet

            row = 0

            worksheet.write(row, 0, "Top Event")
            worksheet.write(row, 1, st.session_state.get("top_event", ""))
            row += 1

            worksheet.write(row, 0, "Deskripsi")
            worksheet.write(row, 1, st.session_state.get("deskripsi_event", ""))
            row += 2

            worksheet.write(row, 0, "Struktur Event")
            row += 1
            df = st.session_state.get(f"copy_{NAMA_TABEL}", pd.DataFrame())
            if not df.empty:
                df.to_excel(writer, sheet_name="Rekap FTA", startrow=row, startcol=0, index=False)
                row += len(df) + 3

            worksheet.write(row, 0, "Probabilitas Top Event")
            worksheet.write(row, 1, str(hitung_probabilitas_manual(df)))
            row += 2

            worksheet.write(row, 0, "Rencana Mitigasi")
            row += 1
            mitigasi = st.session_state.get("mitigasi_df", pd.DataFrame())
            if not mitigasi.empty:
                mitigasi.to_excel(writer, sheet_name="Rekap FTA", startrow=row, startcol=0, index=False)
                row += len(mitigasi) + 3

            worksheet.write(row, 0, "Simulasi Mitigasi")
            row += 1
            simulasi = st.session_state.get("simulasi_df", pd.DataFrame())
            if not simulasi.empty:
                simulasi.to_excel(writer, sheet_name="Rekap FTA", startrow=row, startcol=0, index=False)
                row += len(simulasi) + 3

        st.success(f"✅ File rekap disimpan: {nama_file}")
    except Exception as e:
        st.error(f"❌ Gagal menyimpan: {e}")



# ======================== MAIN ========================
def main():
    global FOLDER_SIMPAN  # ⬅️ agar bisa dipakai di fungsi lain
    FOLDER_SIMPAN = get_user_folder()
    st.title("🌳 Fault Tree Analysis (FTA) dengan Bantuan AI")
    init_session()
    input_top_event()

    if not st.session_state[f"copy_{NAMA_TABEL}"].empty:
        tampilkan_editor()
        tampilkan_visualisasi()
        hitung_probabilitas()
        identifikasi_kontributor()
        rencana_mitigasi()
        simulasi_mitigasi()

   
    if st.button("💾 Simpan & Unduh Rekap (Excel + Gambar)"):
        simpan_ke_excel()
        dot = generate_dot_only()
        simpan_visualisasi(dot)

        nama_top_event = st.session_state.get("top_event", "top_event_kosong").strip().replace(" ", "_")
        tanggal = datetime.now().strftime("%d%m%y")
        nama_file_excel = os.path.join(FOLDER_SIMPAN, f"fault_tree_{nama_top_event}_time_{tanggal}.xlsx")
        nama_file_png = os.path.join(FOLDER_SIMPAN, f"fault_tree_{nama_top_event}_time_{tanggal}.png")

        # 🔥 Buat file ZIP secara in-memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            if os.path.exists(nama_file_excel):
                zipf.write(nama_file_excel, os.path.basename(nama_file_excel))
            if os.path.exists(nama_file_png):
                zipf.write(nama_file_png, os.path.basename(nama_file_png))

        zip_buffer.seek(0)

        st.download_button(
            label="⬇️ Unduh Rekap + Visualisasi (ZIP)",
            data=zip_buffer,
            file_name=f"fault_tree_rekap_{nama_top_event}_{tanggal}.zip",
            mime="application/zip"
        )

        
if __name__ == "__main__":
    main()
