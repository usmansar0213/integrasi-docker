import streamlit as st
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

# Judul aplikasi
st.title("Aplikasi Prediksi dengan Random Forest")

# Langkah 1: Memuat Dataset
st.header("1. Memuat Dataset")
uploaded_file = st.file_uploader("Unggah file CSV Anda", type=["csv"])
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    st.write("Dataset:")
    st.write(data.head())
else:
    st.info("Silakan unggah file CSV untuk melanjutkan.")

# Langkah 2: Penanganan Outlier
st.header("2. Penanganan Outlier")
if uploaded_file is not None:
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    for col in numeric_cols:
        Q1 = data[col].quantile(0.25)
        Q3 = data[col].quantile(0.75)
        IQR = Q3 - Q1
        upper_bound = Q3 + 1.5 * IQR
        outliers = data[col] > upper_bound
        data.loc[outliers, col] = upper_bound
    st.write("Dataset setelah penanganan outlier:")
    st.write(data.head())

# Langkah 3: Pemilihan Variabel Independen dan Dependen
st.header("3. Pemilihan Variabel")
if uploaded_file is not None:
    all_columns = data.columns.tolist()
    target = st.selectbox("Pilih variabel dependen (target):", all_columns)
    features = st.multiselect("Pilih variabel independen (fitur):", all_columns, default=all_columns)
    if target in features:
        features.remove(target)
    st.write(f"Variabel dependen: {target}")
    st.write(f"Variabel independen: {features}")

# Langkah 4: Pembagian Data
st.header("4. Pembagian Data")
if uploaded_file is not None and target and features:
    test_size = st.slider("Pilih ukuran data uji (%):", 10, 50, 20)
    X = data[features]
    y = data[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size/100, random_state=42)
    st.write(f"Ukuran data latih: {X_train.shape[0]} sampel")
    st.write(f"Ukuran data uji: {X_test.shape[0]} sampel")

# Langkah 5: Pelatihan Model Random Forest
st.header("5. Pelatihan Model Random Forest")
if uploaded_file is not None and target and features:
    n_estimators = st.slider("Pilih jumlah pohon dalam hutan:", 10, 200, 100)
    max_depth = st.slider("Pilih kedalaman maksimum pohon:", 1, 20, 10)
    model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    model.fit(X_train, y_train)
    st.success("Model telah dilatih.")

# Langkah 6: Validasi Model dengan MSE dan R²
st.header("6. Validasi Model")
if uploaded_file is not None and target and features:
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    st.write(f"**Mean Squared Error (MSE):** {mse:.4f}")
    st.write(f"**R-squared (R²):** {r2:.4f}")

    # Indikator warna untuk R²
    if r2 >= 0.75:
        r2_color = 'lightgreen'
        r2_status = 'Kuat'
    elif 0.50 <= r2 < 0.75:
        r2_color = 'yellow'
        r2_status = 'Moderat'
    else:
        r2_color = 'red'
        r2_status = 'Lemah'

    # Menampilkan indikator warna
    st.markdown(f"<div style='background-color: {r2_color}; padding: 10px;'>R² Status: {r2_status}</div>", unsafe_allow_html=True)

# Langkah 7: Simulasi Skenario Nilai Tukar USD-RP
st.header("7. Simulasi Skenario")
if uploaded_file is not None and target and features:
    if 'USD-RP' in features:
        usd_rp_value = st.number_input("Masukkan nilai USD-RP untuk simulasi:", value=float(data['USD-RP'].mean()))
        X_simulasi = X_test.copy()
        X_simulasi['USD-RP'] = usd_rp_value
        y_simulasi_pred = model.predict(X_simulasi)
        st.write(f"Prediksi dengan USD-RP = {usd_rp_value}:")
        st.write(y_simulasi_pred)
    else:
        st.warning("Variabel 'USD-RP' tidak ditemukan dalam fitur yang dipilih.")

# Langkah 8: Visualisasi Hasil Prediksi
st.header("8. Visualisasi Hasil Prediksi")
if uploaded_file is not None and target and features:
    fig, ax = plt.subplots()
    ax.scatter(y_test, y_pred, edgecolors=(0, 0, 0))
    ax.plot([y.min(), y.max()], [y.min(), y.max()], 'k--', lw=4)
    ax.set_xlabel('Nilai Aktual')
    ax.set_ylabel('Nilai Prediksi')
    ax.set_title('Perbandingan Nilai Aktual vs. Prediksi')
    st.pyplot(fig)
