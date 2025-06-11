import os
import openai
import streamlit as st



def main():
    # Konfigurasi API OpenAI dari environment variable
   openai.api_key = st.secrets["openai_api_key"]

    # 1. Judul Aplikasi
    col1, col2 = st.columns([1, 10])

    # Path logo relatif agar bisa digunakan di mana saja
    logo_path = os.path.join("static", "via_icon.jpg")

    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
            st.warning("Logo tidak ditemukan di folder static/")

    with col2:
        st.title("Altman Z-Score Calculator with AI Evaluation")

    st.markdown("""
    Aplikasi ini digunakan untuk menghitung **Altman Z-Score**, sebuah indikator untuk menilai risiko kebangkrutan perusahaan.
    Masukkan data keuangan perusahaan pada form berikut untuk mendapatkan hasil, analisis, dan kesimpulan dari AI.
    """)

    # 2. Penjelasan Indikator Altman Z-Score
    st.header("1. Penjelasan Indikator Altman Z-Score")
    st.markdown("""
    **Altman Z-Score** adalah skor keuangan yang digunakan untuk memprediksi risiko kebangkrutan perusahaan berdasarkan rasio keuangan utama. Berikut adalah formula Z-Score:
    """)

    company_type = st.radio("Pilih Jenis Perusahaan:", ("Manufaktur", "Non-Manufaktur"))

    if company_type == "Manufaktur":
        st.latex(r"Z = 1.2X_1 + 1.4X_2 + 3.3X_3 + 0.6X_4 + 1.0X_5")
        st.markdown("""Formula ini digunakan untuk perusahaan manufaktur.""")
    else:
        st.latex(r"Z = 6.56X_1 + 3.26X_2 + 6.72X_3 + 1.05X_4")
        st.markdown("""Formula ini digunakan untuk perusahaan non-manufaktur.""")

    st.latex(r"X_1 = \frac{\text{Modal Kerja}}{\text{Total Aset}}")
    st.markdown("Mengukur likuiditas perusahaan dalam jangka pendek.")
    
    st.latex(r"X_2 = \frac{\text{Laba Ditahan}}{\text{Total Aset}}")
    st.markdown("Mengindikasikan laba yang diinvestasikan kembali ke perusahaan.")
    
    st.latex(r"X_3 = \frac{\text{EBIT}}{\text{Total Aset}}")
    st.markdown("Menilai profitabilitas perusahaan dari aset yang dimiliki.")
    
    st.latex(r"X_4 = \frac{\text{Nilai Pasar Ekuitas}}{\text{Total Kewajiban}}")
    st.markdown("Rasio antara nilai pasar ekuitas dengan total kewajiban untuk menunjukkan solvabilitas.")
    
    if company_type == "Manufaktur":
        st.latex(r"X_5 = \frac{\text{Penjualan}}{\text{Total Aset}}")
        st.markdown("Efisiensi penggunaan aset untuk menghasilkan penjualan.")

    st.markdown("""
    ### Interpretasi Skor:
    - **Z > 2.99**: Zona Aman (tidak berisiko kebangkrutan).
    - **1.81 < Z < 2.99**: Zona Abu-Abu (risiko sedang).
    - **Z < 1.81**: Risiko Tinggi (kemungkinan besar perusahaan menghadapi kebangkrutan).
    """)

    # 3. Input Data Keuangan
    st.header("2. Input Data Keuangan")

    working_capital = st.number_input("Modal Kerja (Working Capital)", min_value=0.0, step=1000.0, help="Selisih antara aset lancar dan kewajiban lancar.")
    total_assets = st.number_input("Total Aset (Total Assets)", min_value=1.0, step=1000.0, help="Total keseluruhan aset perusahaan.")
    retained_earnings = st.number_input("Laba Ditahan (Retained Earnings)", min_value=0.0, step=1000.0, help="Akumulasi laba bersih yang disimpan perusahaan.")
    ebit = st.number_input("EBIT (Laba Operasional)", min_value=0.0, step=1000.0, help="Laba sebelum bunga dan pajak dikurangkan.")
    market_value_equity = st.number_input("Nilai Pasar Ekuitas (Market Value of Equity)", min_value=0.0, step=1000.0, help="Kapitalisasi pasar perusahaan (harga saham × jumlah saham).")
    total_liabilities = st.number_input("Total Kewajiban (Total Liabilities)", min_value=1.0, step=1000.0, help="Total kewajiban perusahaan, termasuk kewajiban jangka pendek dan panjang.")

    if company_type == "Manufaktur":
        sales = st.number_input("Penjualan (Sales)", min_value=0.0, step=1000.0, help="Total pendapatan dari penjualan barang atau jasa.")

    # 4. Validasi Data Input
    st.header("3. Validasi Data")
    if total_assets <= 0 or total_liabilities <= 0:
        st.error("Total Aset dan Total Kewajiban harus lebih besar dari nol.")
        return

    if any(value == 0 for value in [working_capital, retained_earnings, ebit, market_value_equity]) or (company_type == "Manufaktur" and sales == 0):
        st.warning("Beberapa nilai masukan adalah nol. Pastikan semua nilai sudah diisi untuk hasil yang akurat.")

    # 5. Kalkulasi Altman Z-Score
    st.header("4. Hasil Perhitungan Altman Z-Score")
    if st.button("Hitung Z-Score"):
        try:
            # Perhitungan Komponen Z-Score
            x1 = working_capital / total_assets
            x2 = retained_earnings / total_assets
            x3 = ebit / total_assets
            x4 = market_value_equity / total_liabilities

            if company_type == "Manufaktur":
                x5 = sales / total_assets
                z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
            else:
                z_score = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4

            # Interpretasi dan Indikator Warna
            if z_score > 2.99:
                interpretation = "Zona Aman (Tidak Berisiko)"
                color = "green"
            elif z_score > 1.81:
                interpretation = "Zona Abu-Abu (Risiko Sedang)"
                color = "yellow"
            else:
                interpretation = "Risiko Tinggi (Potensi Kebangkrutan)"
                color = "red"

            # Menampilkan Hasil dengan Indikator Warna
            st.markdown(
                f"<h3>Z-Score: <span style='color:{color}'>{z_score:.2f}</span></h3>",
                unsafe_allow_html=True
            )
            st.markdown(f"**Interpretasi:** {interpretation}")

            # 6. Evaluasi dengan GPT
            st.header("5. Kesimpulan dan Evaluasi AI")
            with st.spinner("Sedang menganalisis data dengan AI..."):
                prompt = f"""
                Sebuah perusahaan memiliki Altman Z-Score sebesar {z_score:.2f}, yang tergolong dalam {interpretation}.
                Berikut data keuangannya:
                - Modal Kerja: {working_capital}
                - Total Aset: {total_assets}
                - Laba Ditahan: {retained_earnings}
                - EBIT: {ebit}
                - Nilai Pasar Ekuitas: {market_value_equity}
                - Total Kewajiban: {total_liabilities}
                - Penjualan: {sales if company_type == 'Manufaktur' else 'N/A'}

                Berikan evaluasi mendalam terhadap kondisi keuangan perusahaan, potensi risiko kebangkrutan, 
                dan saran strategis untuk meningkatkan kinerja perusahaan berdasarkan data tersebut.
                """
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",  # Anda dapat mengganti ke "gpt-4" jika memiliki akses
                    messages=[
                        {"role": "system", "content": "Anda adalah analis keuangan yang berpengalaman."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                analysis = response['choices'][0]['message']['content'].strip()

            st.success("Analisis selesai!")
            st.markdown(f"### Evaluasi AI:\n{analysis}")

        except ZeroDivisionError:
            st.error("Pastikan semua nilai sudah diisi dengan benar dan Total Aset/Kewajiban tidak nol.")

    # 7. Catatan
    st.header("6. Catatan")
    st.info("Pastikan semua data keuangan diinput dengan benar untuk mendapatkan hasil yang akurat.")
