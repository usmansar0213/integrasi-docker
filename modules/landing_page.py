import streamlit as st
import os

def show():
    # ------------------ Tampilan Atas dengan VIA Icon ------------------ #
    col1, col2 = st.columns([2, 8])
    via_icon_path = os.path.join("static", "via_icon.jpg")
    with col1:
        if os.path.exists(via_icon_path):
            st.image(via_icon_path, width=150)
    with col2:
        st.markdown("## Selamat Datang di Aplikasi RISMA")
        st.markdown("### Platform Manajemen Risiko Terpadu – Proyek & Korporasi")

    st.markdown("---")

    # ------------------ Penjelasan Umum ------------------ #
    st.markdown("""
    Aplikasi **RISMA** menggabungkan dua pilar utama dalam manajemen risiko:

    - 🎛️ **MR Tools** – Alat bantu berbasis AI untuk eksplorasi dan analisis risiko secara cepat dan fleksibel
    - 🧠 **PRIMA-Ai** – Sistem manajemen risiko enterprise yang sesuai regulasi PER-2/MBU/03/2023

    ---
    """)

    # ------------------ MR Tools ------------------ #
    st.subheader("🧰 MR Tools – AI & Analitik untuk Risiko")
    st.markdown("""
    Modul-modul ini berfungsi sebagai **alat bantu berbasis AI dan data science**:

    1. 🤖 **Chat Bot RISMA** – Asisten AI untuk analisis risiko dan tanya jawab
    2. 🎲 **Risk Modeling Monte Carlo** – Simulasi risiko berbasis distribusi probabilistik
    3. 🧠 **RCSA AI** – Identifikasi mandiri risiko dan kontrol secara otomatis
    4. 📊 **Feasibility Study** – Studi kelayakan proyek secara menyeluruh
    5. 💣 **Stress Testing** – Uji ketahanan perusahaan terhadap skenario ekstrem
    6. 🧮 **Altman Z-Score** – Prediksi potensi kebangkrutan berdasarkan rasio keuangan
    7. 📈 **Risk Maturity Index** – Evaluasi kematangan sistem manajemen risiko
    8. 🌳 **Fault Tree Analysis (FTA)** – Analisis pohon kesalahan untuk mengidentifikasi akar penyebab risiko


    > Cocok untuk: analis risiko, pengambil keputusan proyek, tim AI & data science.
    """)

    st.subheader("🏛️ PRIMA-Ai – Sistem Risiko Berbasis Regulasi")
    st.markdown("""
    PRIMA-Ai dirancang untuk mengelola risiko **secara korporat** sesuai standar BUMN:

    1. 📊 **Dashboard Otomatis** – Visualisasi ringkasan semua aktivitas risiko  
    2. 🏢 **Profil Perusahaan** – Informasi dasar unit kerja, struktur, aset  
    3. 📌 **Strategi Risiko & Appetite** – Penetapan batas & kebijakan risiko  
    4. 🎯 **Sasaran Strategi Bisnis** – Tujuan strategis sebagai acuan risiko  
    5. 📋 **Profil Risiko & KRI** – Identifikasi risiko dan indikator kunci  
    6. 🧮 **Risiko Inherent** – Perhitungan risiko awal  
    7. ⚖️ **Risiko Residual** – Risiko tersisa setelah mitigasi  
    8. 🛠️ **Perlakuan Risiko** – Rekomendasi mitigasi otomatis oleh AI  
    9. 💰 **Risk-Based Budgeting** – Alokasi anggaran mitigasi berbasis risiko  
    10. 🌡️ **Heatmap Risiko** – Visualisasi level risiko (Matriks Warna)  
    11. 📆 **Detail Perlakuan Risiko** – Rencana kerja mitigasi per kuartal  
    12. 📅 **Monitoring & Evaluasi** – Update bulanan efektivitas mitigasi  
    13. 🧾 **Loss Event** – Pencatatan kejadian kerugian aktual dan dampaknya  
    14. 📘 **Organ & Kualifikasi** – Pendataan organ pengelola risiko dan kualifikasinya  
    15. 🧩 **Modul Integrasi Data** – Integrasi data monitoring seluruh unit

    > Cocok untuk: Satuan Manajemen Risiko, Compliance Unit, dan Pemimpin Korporat.
    """)

    st.success("🧭 Silakan pilih salah satu menu modul dari sidebar kiri untuk memulai.")
    st.info("💡 Tips: Anda bisa kembali ke halaman ini kapan saja melalui menu *Landing Page*.")

