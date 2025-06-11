import streamlit as st
import numpy as np
import pandas as pd
import os

def main():
    import streamlit as st
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import numpy_financial as npf
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error
    from st_aggrid import AgGrid, GridOptionsBuilder
    from scipy.optimize import newton

    
    # Inisialisasi session state jika belum ada
    if 'investment_data' not in st.session_state:
        st.session_state['investment_data'] = {
            'judul_investasi': "Investasi Saham",
            'currency': "USD",
            'initial_investment': 5000,
            'risk_tolerance': "Menengah",
            'investment_goal': "Pendapatan pasif"
        }

    # Judul Utama dengan Ikon
    col1, col2 = st.columns([1, 10])

    # Path relatif ke logo
    logo_path = os.path.join("static", "via_icon.jpg")

    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
            st.warning("Logo tidak ditemukan di folder static/")

    with col2:
        st.title("Studi Kelayakan Proyek")

    # Input nama investasi dengan default dari session_state
    judul_default = st.session_state.get('investment_data', {}).get('judul_investasi', '')
    judul_investasi = st.text_input("Masukkan nama investasi:", value=judul_default)

    st.subheader(f"{judul_investasi}")

    # Langkah 1: Masukkan Informasi Rencana Investasi
    st.header("1. Informasi Rencana Investasi")

    # Input untuk mata uang dan modal awal
    mata_uang = st.selectbox(
        "Pilih mata uang:",
        ["USD", "Rupiah"],
        index=["USD", "Rupiah"].index(st.session_state['investment_data']['currency'])
    )
    modal = st.number_input(
        f"Berapa jumlah dana yang ingin Anda investasikan pada {judul_investasi} (dalam {mata_uang})?",
        min_value=1,
        value=st.session_state['investment_data']['initial_investment']
    )

    # Input toleransi risiko dan tujuan investasi
    toleransi_risiko = st.radio(
        "Seberapa besar risiko yang bersedia Anda tanggung?",
        ("Rendah", "Menengah", "Tinggi"),
        index=["Rendah", "Menengah", "Tinggi"].index(st.session_state['investment_data']['risk_tolerance'])
    )
    tujuan_investasi = st.selectbox(
        "Apa tujuan utama dari investasi ini?",
        ("Pendapatan pasif", "Pertumbuhan modal", "Diversifikasi portfolio"),
        index=["Pendapatan pasif", "Pertumbuhan modal", "Diversifikasi portfolio"].index(st.session_state['investment_data']['investment_goal'])
    )

    # Simpan data ke `st.session_state`
    st.session_state['investment_data']['judul_investasi'] = judul_investasi
    st.session_state['investment_data']['currency'] = mata_uang
    st.session_state['investment_data']['initial_investment'] = modal
    st.session_state['investment_data']['risk_tolerance'] = toleransi_risiko
    st.session_state['investment_data']['investment_goal'] = tujuan_investasi

        
    # Langkah 2: Input untuk analisis SWOT
    st.header("2. Analisis SWOT")

    # Menyediakan contoh untuk analisis SWOT umum
    st.subheader("Kekuatan (Strengths)")
    kekuatan_contoh = """
    - **Keunggulan Kompetitif**: Memiliki pasar yang kuat dan loyalitas pelanggan.
    - **Diversifikasi Pendapatan**: Sumber pendapatan yang bervariasi.
    - **Inovasi Berkelanjutan**: Investasi yang konsisten dalam teknologi dan produk baru.
    """
    kekuatan = st.text_area("Masukkan Kekuatan (Strengths):", value=kekuatan_contoh, height=150)

    st.subheader("Kelemahan (Weaknesses)")
    kelemahan_contoh = """
    - **Ketergantungan pada Segmen Utama**: Pendapatan signifikan berasal dari satu segmen utama.
    - **Masalah Regulasi**: Tantangan terkait dengan kepatuhan hukum dan peraturan.
    - **Biaya Operasional Tinggi**: Profitabilitas dapat terpengaruh oleh biaya operasional.
    """
    kelemahan = st.text_area("Masukkan Kelemahan (Weaknesses):", value=kelemahan_contoh, height=150)

    st.subheader("Peluang (Opportunities)")
    peluang_contoh = """
    - **Ekspansi Pasar Baru**: Potensi untuk memasuki pasar baru.
    - **Pertumbuhan Industri**: Tren positif di sektor terkait.
    - **Kemitraan Strategis**: Peluang untuk bermitra dengan pemain besar lainnya.
    """
    peluang = st.text_area("Masukkan Peluang (Opportunities):", value=peluang_contoh, height=150)

    st.subheader("Ancaman (Threats)")
    ancaman_contoh = """
    - **Persaingan yang Ketat**: Hadirnya pesaing besar di pasar.
    - **Perubahan Regulasi**: Kebijakan pemerintah yang dapat memengaruhi operasi.
    - **Fluktuasi Ekonomi**: Ketidakpastian ekonomi global yang dapat memengaruhi permintaan.
    """
    ancaman = st.text_area("Masukkan Ancaman (Threats):", value=ancaman_contoh, height=150)


    st.header("3. Asumsi Evaluasi Finansial")

    # Tabel asumsi finansial yang dapat diedit oleh pengguna
    file_diupload = st.file_uploader("Upload CSV untuk Asumsi Finansial (Opsional):", type=["csv"])
    if file_diupload is not None:
        asumsi_df = pd.read_csv(file_diupload)
    else:
        # Gunakan mata uang dari session state (default "USD" jika tidak tersedia)
        mata_uang = st.session_state.get('currency', "USD")
        data_asumsi = {
            'Asumsi': [
                'Tingkat Pertumbuhan Laba Bersih (%)',
                'Tingkat Pembayaran Dividen (%)',
                'Tingkat Diskonto (%)',
                'Tingkat Inflasi (%)',
                'Tingkat Suku Bunga (%)',
                f'Harga Saat Ini ',
                f'Estimasi Laba Bersih Tahun Pertama'
            ],
            'Nilai': [5.0, 30.0, 10.0, 2.0, 3.0, 100, 1.0]
        }
        asumsi_df = pd.DataFrame(data_asumsi)

    # Konfigurasi AgGrid untuk memungkinkan pengeditan
    gb = GridOptionsBuilder.from_dataframe(asumsi_df)
    gb.configure_default_column(editable=True)
    gb.configure_grid_options(domLayout='normal')  # Menambahkan pengaturan tinggi tabel
    opsi_grid = gb.build()

    # Menampilkan tabel interaktif menggunakan AgGrid
    data_diedit = AgGrid(
        asumsi_df,
        gridOptions=opsi_grid,
        update_mode="MODEL_CHANGED",
        fit_columns_on_grid_load=True,
        height=250  # Menentukan tinggi tabel dalam piksel
    )

    asumsi_diperbarui_df = pd.DataFrame(data_diedit['data'])


    st.header("4. Upload Data History Perusahaan")
    file_diupload = st.file_uploader("Upload file Excel", type=["xlsx"])
    if file_diupload:
        df = pd.read_excel(file_diupload)
        st.write("Data yang diupload:", df.head())

        # Mencari nama kolom tahun
        year_column = None
        for col in df.columns:
            if col.lower() in ['year', 'tahun']:
                year_column = col
                break

        if year_column is None:
            st.warning("Kolom 'Year' atau 'Tahun' tidak ditemukan. Silakan pilih kolom yang sesuai.")
            year_column = st.selectbox("Pilih kolom yang mewakili tahun:", df.columns)

        if year_column:
            variabel = [col for col in df.columns if col != year_column]
            variabel_tergantung = st.selectbox("Pilih dependent variable:", variabel, key="dependent_var")
            variabel_mandiri = st.multiselect("Pilih independent variables:", variabel, key="independent_vars")

            if variabel_mandiri and variabel_tergantung:
                st.subheader("Langkah 2: Input Target Value")
                nilai_target = st.slider("Masukkan Target Value:", min_value=-10000.0, max_value=10000.0, value=5.0, step=0.1, key="target_value")

                tahun_terakhir = df[year_column].max()
                tahun_prediksi = st.slider("Tahun untuk diprediksi:", 1, 20, 10, key="prediction_years")
                tahun_mendatang = np.array(range(tahun_terakhir + 1, tahun_terakhir + 1 + tahun_prediksi)).reshape(-1, 1)

                if st.button("Proses Data", key="process_data"):
                    # Simpan data ke session state
                    st.session_state['data_asumsi'] = asumsi_diperbarui_df
                    st.session_state['data_history'] = df

                    # Lakukan simulasi
                    prediksi = {}
                    variabel_disesuaikan = []

                    for var in variabel_mandiri:
                        model = LinearRegression()
                        asumsi_terkait = st.session_state['data_asumsi'][
                            st.session_state['data_asumsi']['Asumsi'].str.contains(var, case=False, na=False)]
                        if not asumsi_terkait.empty:
                            st.write(f"Menggunakan asumsi terkait untuk {var}: {asumsi_terkait.iloc[0]['Nilai']}")
                            variabel_disesuaikan.append(var)

                        model.fit(df[[year_column]], df[var])
                        prediksi[var] = model.predict(tahun_mendatang)

                    data_histori = df[[year_column] + variabel_mandiri].sort_values(by=year_column, ascending=False)
                    data_mendatang = pd.DataFrame({year_column: tahun_mendatang.flatten(), **prediksi})
                    gabungan_df = pd.concat([data_histori, data_mendatang], ignore_index=True).sort_values(by=year_column, ascending=False)

                    st.session_state['processed_data'] = gabungan_df

                    # Tampilkan data gabungan
                    st.subheader("Data Gabungan")
                    opsi_grid = GridOptionsBuilder.from_dataframe(gabungan_df)
                    opsi_grid.configure_default_column(editable=True)
                    konfigurasi_grid = opsi_grid.build()
                    AgGrid(
                        gabungan_df,
                        gridOptions=konfigurasi_grid,
                        update_mode='MODEL_CHANGED',
                        allow_unsafe_jscode=True
                    )

                    if variabel_disesuaikan:
                        st.subheader("Variabel yang Disesuaikan")
                        for var in variabel_disesuaikan:
                            st.write(f"- {var}")
                    else:
                        st.write("Tidak ada variabel yang disesuaikan dengan asumsi.")

                st.header("Langkah 5: Regresi dan Simulasi Monte Carlo")
                # Define variables from user selection
                independent_variables = variabel_mandiri  # Variables selected earlier in multiselect
                dependent_variable = variabel_tergantung  # Variable selected earlier in selectbox

                # Ensure variables are defined
                if not independent_variables or not dependent_variable:
                    st.error("Please select both independent and dependent variables before proceeding.")
                else:
                    # Simulasi Regresi Linear
                    model_regresi = LinearRegression()
                    model_regresi.fit(df[independent_variables], df[dependent_variable])

                    jumlah_simulasi = st.number_input("Masukkan jumlah simulasi:", min_value=100, step=100, value=1000)

                    hasil_monte_carlo = []
                    for _ in range(jumlah_simulasi):
                        nilai_simulasi = {}
                        for i, var in enumerate(independent_variables):
                            nilai_simulasi[var] = np.random.normal(df[var].mean(), df[var].std(), 1)[0]
                        nilai_prediksi = model_regresi.intercept_ + sum(
                            model_regresi.coef_[i] * nilai_simulasi[var] for i, var in enumerate(independent_variables)
                        )
                        hasil_monte_carlo.append(nilai_prediksi)

                    r_squared = model_regresi.score(df[independent_variables], df[dependent_variable])
                    tingkat_kepercayaan = 5
                    var = np.percentile(hasil_monte_carlo, tingkat_kepercayaan)

                    monte_carlo_bulat = [round(value) for value in hasil_monte_carlo]
                    nilai_unik, jumlah = np.unique(monte_carlo_bulat, return_counts=True)
                    probabilitas_relatif = jumlah / jumlah_simulasi

                    # Visualisasi dan Metrik
                    st.subheader("Visualisasi dan Metrik")
                    plt.figure(figsize=(10, 6))
                    plt.hist(hasil_monte_carlo, bins=30, color='blue', alpha=0.7)
                    plt.title("Hasil Simulasi Monte Carlo")
                    plt.xlabel(dependent_variable)
                    plt.ylabel("Frekuensi")
                    st.pyplot(plt)

                    st.write(f"Rata-rata hasil simulasi: {np.mean(hasil_monte_carlo):.2f}")
                    st.write(f"Standar deviasi hasil simulasi: {np.std(hasil_monte_carlo):.2f}")
                    st.write(f"R-Squared dari model regresi: {r_squared:.2f}")
                    st.write(f"Value at Risk (VaR) pada level {tingkat_kepercayaan}%: {var:.2f}")

                st.subheader("Langkah 6: Nilai Prediksi dari Waktu ke Waktu")
                # Gabungkan data historis dan data prediksi untuk Random Forest
                tahun_historis = df[year_column].values
                tahun_prediksi = tahun_mendatang.flatten()[:len(hasil_monte_carlo)]  # Sesuaikan panjang hasil Monte Carlo
                semua_tahun = np.concatenate([tahun_historis, tahun_prediksi])

                y = np.concatenate([df[dependent_variable].values, hasil_monte_carlo[:len(tahun_prediksi)]])  # Sesuaikan panjang
                X = semua_tahun.reshape(-1, 1)  # Gunakan tahun sebagai fitur

                # Bagi data
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

                # Latih Random Forest Regressor
                model_rf = RandomForestRegressor(n_estimators=100, random_state=42)
                model_rf.fit(X_train, y_train)

                # Buat prediksi
                prediksi = model_rf.predict(X)

                # Hitung MSE
                mse = mean_squared_error(y_test, model_rf.predict(X_test))
                st.write(f"Mean Squared Error: {mse:.2f}")

                # Summary Plot Data Historis dan Prediksi
                plt.figure(figsize=(12, 6))
                plt.plot(tahun_historis, df[dependent_variable].values, label="Data Historis", color="blue")
                plt.plot(tahun_prediksi, hasil_monte_carlo[:len(tahun_prediksi)], label="Prediksi Monte Carlo", color="orange", linestyle="--")
                plt.plot(semua_tahun, prediksi, label="Prediksi Random Forest", color="green")
                plt.xlabel("Tahun")
                plt.ylabel(dependent_variable)
                plt.title("Nilai Prediksi dari Waktu ke Waktu")
                plt.legend()
                st.pyplot(plt)

                summary_plot = {
                    "tahun_historis": tahun_historis.tolist(),
                    "data_historis": df[dependent_variable].values.tolist(),
                    "tahun_prediksi": tahun_prediksi.tolist(),
                    "monte_carlo": hasil_monte_carlo[:len(tahun_prediksi)],
                    "prediksi_rf": prediksi.tolist()
                }

                # Gabungkan data historis dan prediksi untuk gabungan_df
                gabungan_df = pd.DataFrame({
                    'Year': semua_tahun,
                    'Value': np.concatenate([df[dependent_variable].values, prediksi[len(tahun_historis):]])
                })

                # Simpan data ke session state
                st.session_state['gabungan_df'] = gabungan_df
                st.session_state['summary_monte_carlo'] = {
                    "r_squared": r_squared,
                    "mean": np.mean(hasil_monte_carlo),
                    "std_dev": np.std(hasil_monte_carlo),
                    "VaR": var
                }
                st.session_state['summary_plot'] = summary_plot

               
                # Tampilkan Summary Plot
                data_summary = {
                    "Kategori": ["Data Historis", "Monte Carlo", "Random Forest"],
                    "Rata-Rata": [
                        np.mean(df[dependent_variable].values),
                        np.mean(hasil_monte_carlo[:len(tahun_prediksi)]),
                        np.mean(prediksi[len(tahun_historis):])
                    ],
                    "Standar Deviasi": [
                        np.std(df[dependent_variable].values),
                        np.std(hasil_monte_carlo[:len(tahun_prediksi)]),
                        np.std(prediksi[len(tahun_historis):])
                    ],
                    "Nilai Minimum": [
                        np.min(df[dependent_variable].values),
                        np.min(hasil_monte_carlo[:len(tahun_prediksi)]),
                        np.min(prediksi[len(tahun_historis):])
                    ],
                    "Nilai Maksimum": [
                        np.max(df[dependent_variable].values),
                        np.max(hasil_monte_carlo[:len(tahun_prediksi)]),
                        np.max(prediksi[len(tahun_historis):])
                    ]
                }
                data_summary_df = pd.DataFrame(data_summary)
                st.subheader("Summary: Data Historis dan Prediksi")
                st.table(data_summary_df)

                # Evaluasi Keuangan
                # Evaluasi Keuangan
                st.subheader("7. Evaluasi Keuangan: IRR, NPV, dan Payback Period")

                # Ambil nilai initial investment dan currency dari session state
                initial_investment = st.session_state['investment_data']['initial_investment']
                currency = st.session_state['investment_data']['currency']
                discount_rate = 0.1  # Tingkat diskonto default (10%)
                cash_flows = summary_plot['monte_carlo']  # Gunakan prediksi Monte Carlo untuk cash flow

                # Perhitungan NPV
                st.write("### Net Present Value (NPV)")
                st.write("**Rumus:**")
                st.latex(r"NPV = \sum_{t=1}^{n} \frac{CF_t}{(1 + r)^t} - C_0")
                st.write("**Komponen dan Nilai:**")
                st.write(f"- Modal Awal \(C_0\): {initial_investment:.2f} {currency}")
                st.write(f"- Tingkat Diskonto \(r\): {discount_rate:.2%}")
                st.write(f"- Cash Flows \(CF_t\): {cash_flows}")

                npv = npf.npv(discount_rate, [-initial_investment] + cash_flows)
                st.write(f"**Hasil NPV:** {npv:.2f} {currency}")
                if npv > 0:
                    st.success("Proyek ini menguntungkan berdasarkan perhitungan NPV.")
                else:
                    st.warning("Proyek ini tidak menguntungkan berdasarkan perhitungan NPV.")

                # Perhitungan IRR
                st.write("### Internal Rate of Return (IRR)")
                st.write("**Rumus:**")
                st.latex(r"NPV = \sum_{t=1}^{n} \frac{CF_t}{(1 + IRR)^t} - C_0 = 0")
                st.write("**Komponen dan Nilai:**")
                st.write(f"- Modal Awal \(C_0\): {initial_investment:.2f} {currency}")
                st.write(f"- Cash Flows \(CF_t\): {cash_flows}")

                irr = npf.irr([-initial_investment] + cash_flows)
                st.write(f"**Hasil IRR:** {irr:.2%}")
                if irr > discount_rate:
                    st.success("Proyek ini layak karena IRR lebih besar dari tingkat diskonto.")
                else:
                    st.warning("Proyek ini tidak layak karena IRR lebih kecil dari tingkat diskonto.")

                # Perhitungan Payback Period
                st.write("### Payback Period")
                st.write("**Definisi:** Waktu yang diperlukan hingga arus kas kumulatif \(\geq 0\).")
                st.write("**Komponen dan Nilai:**")
                st.write(f"- Modal Awal \(C_0\): {initial_investment:.2f} {currency}")
                st.write(f"- Cash Flows \(CF_t\): {cash_flows}")

                cumulative_cash_flow = np.cumsum([-initial_investment] + cash_flows)
                payback_period = next((i for i, cf in enumerate(cumulative_cash_flow) if cf >= 0), None)

                if payback_period is not None:
                    st.write(f"**Hasil Payback Period:** {payback_period} tahun")
                    if payback_period <= len(cash_flows):
                        st.success("Proyek ini layak karena Payback Period tercapai dalam durasi prediksi.")
                    else:
                        st.warning("Proyek ini tidak layak karena Payback Period terlalu panjang.")
                else:
                    st.warning("Payback Period tidak tercapai dalam durasi prediksi.")

                # Rekomendasi
                st.write("### Rekomendasi")
                if npv > 0 and irr > discount_rate and payback_period is not None and payback_period <= len(cash_flows):
                    st.success("Proyek ini direkomendasikan untuk dijalankan berdasarkan evaluasi keuangan.")
                else:
                    st.warning("Proyek ini tidak direkomendasikan untuk dijalankan berdasarkan evaluasi keuangan.")
