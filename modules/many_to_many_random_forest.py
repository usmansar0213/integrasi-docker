import streamlit as st
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.metrics import mean_squared_error, r2_score
from st_aggrid import AgGrid, GridOptionsBuilder
from sklearn.ensemble import RandomForestRegressor


# Judul aplikasi
st.title("Aplikasi Prediksi dengan Random Forest")

# Langkah 1: Memuat Dataset
default_file_path = "C:\\project 2\\Database Montecarlo\\Sort_All_Variable.xlsx"

st.header("1. Memuat Dataset")
uploaded_file = st.file_uploader("Unggah file Excel atau CSV Anda", type=["csv", "xlsx"])
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            data = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            data = pd.read_excel(uploaded_file)
        st.write("Dataset yang diunggah:")
        st.write(data.head())
    except Exception as e:
        st.error(f"Gagal memuat dataset. Pastikan file memiliki format yang benar. Error: {e}")
else:
    try:
        data = pd.read_excel(default_file_path)
        st.write(f"Dataset default yang dimuat dari: {default_file_path}")
        st.write(data.head())
    except Exception as e:
        st.error(f"Gagal memuat dataset default. Pastikan file tersedia. Error: {e}")

# Langkah 2: Penanganan Outlier
st.header("2. Penanganan Outlier")
if 'data' in locals():
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
if 'data' in locals():
    all_columns = data.columns.tolist()
    default_targets = ["TOTAL LIABILITAS_C", "Pendapatan Operasi_C", "BOPO", "Beban Keuangan_C", "Arus Kapal", "Arus Petikemas", "Arus Barang", "Arus Penumpang"]
    targets = st.multiselect("Pilih variabel dependen (target):", all_columns, default=[col for col in default_targets if col in all_columns])
    features = st.multiselect("Pilih variabel independen (fitur):", all_columns, default=all_columns)
    for target in targets:
        if target in features:
            features.remove(target)

# Langkah  Pembagian Data
if 'data' in locals() and targets and features:
    test_size = st.slider("Pilih ukuran data uji (%):", 10, 50, 20, key="test_size")
    X = data[features]
    y = data[targets]

    # Feature Engineering untuk interaksi berbasis variabel lain
    interaction_variables = ['USD-RP', 'Harga Batu Bara', 'Fed Rate']  # Tambahkan variabel interaksi lain sesuai kebutuhan
    for interaction_var in interaction_variables:
        if interaction_var in features:
            for feature in features:
                if feature != interaction_var:
                    interaction_feature = f"{feature}_x_{interaction_var}"
                    X[interaction_feature] = X[feature] * X[interaction_var]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size/100, random_state=42)

# Tampilkan Data History Sebelum Prediksi
st.header("4. Data History")
st.write("Data history yang digunakan untuk pelatihan:")
st.write(X_train.head())


# --- PASTIKAN SEMUA KOLOM NUMERIK ---
for col in X.columns:
    X[col] = pd.to_numeric(X[col], errors='coerce')

# --- FITUR INTERAKSI (dengan pengecekan error dan numerik) ---
interaction_variables = ['USD-RP', 'Harga Batu Bara', 'Fed Rate']  # Sesuaikan jika ada
for interaction_var in interaction_variables:
    if interaction_var in features:
        for feature in features:
            if feature != interaction_var:
                interaction_feature = f"{feature}_x_{interaction_var}"
                try:
                    if pd.api.types.is_numeric_dtype(X[feature]) and pd.api.types.is_numeric_dtype(X[interaction_var]):
                        X[interaction_feature] = X[feature] * X[interaction_var]
                    else:
                        st.warning(f"Lewati interaksi: {interaction_feature} karena salah satu kolom bukan numerik.")
                except Exception as e:
                    st.warning(f"Gagal membuat fitur interaksi: {interaction_feature} karena: {e}")

# --- Tampilkan tipe data (opsional debug) ---
st.subheader("📊 Tipe Data Kolom")
st.write(X.dtypes)

# --- Split Data ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size/100, random_state=42)

# --- Tangani NaN jika ada akibat interaksi ---
X_train = X_train.fillna(0)
X_test = X_test.fillna(0)

# --- Tampilkan Data Tambahan dari Interaction Variables ---
st.header("5. Data Interaction Variables")
st.write("Fitur interaksi yang dihasilkan:")
interaction_columns = [col for col in X.columns if '_x_' in col]
if interaction_columns:
    st.write(X[interaction_columns].head())
else:
    st.write("Tidak ada fitur interaksi yang dihasilkan.")

# --- Pelatihan Model Random Forest (Regressor atau Classifier) ---
st.header("6. Pelatihan Model Random Forest")
if 'data' in locals() and targets and features:
    n_estimators = st.slider("Pilih jumlah pohon dalam hutan:", 10, 200, 100)
    max_depth = st.slider("Pilih kedalaman maksimum pohon:", 1, 20, 10)

    models = {}
    for target in targets:
        if y_train[target].dropna().nunique() <= 2:
            # Klasifikasi jika target hanya 0/1
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42, class_weight='balanced')
        else:
            # Regresi jika target numerik
            model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)

        model.fit(X_train, y_train[target])
        models[target] = model
    st.success("Model telah dilatih untuk semua variabel dependen.")

# --- Validasi Model (Regresi atau Klasifikasi) ---
st.header("7. Validasi Model")
if 'data' in locals() and targets and features:
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

    results = []
    for target in targets:
        y_pred = models[target].predict(X_test)

        if y_train[target].dropna().nunique() <= 2:
            # Klasifikasi
            acc = accuracy_score(y_test[target], y_pred)
            report = classification_report(y_test[target], y_pred, output_dict=True, zero_division=0)
            cm = confusion_matrix(y_test[target], y_pred)

            precision = report['macro avg']['precision']
            recall = report['macro avg']['recall']

            results.append({
                "Target": target,
                "Accuracy": acc,
                "Precision (macro avg)": precision,
                "Recall (macro avg)": recall,
                "Confusion Matrix": cm.tolist()
            })
        else:
            # Regresi
            from sklearn.metrics import mean_squared_error, r2_score
            mse = mean_squared_error(y_test[target], y_pred)
            r2 = r2_score(y_test[target], y_pred)
            results.append({
                "Target": target,
                "MSE": mse,
                "R²": r2
            })

    results_df = pd.DataFrame(results)
    st.write("Hasil Validasi:")
    st.dataframe(results_df.drop(columns=['Confusion Matrix'], errors='ignore'), use_container_width=True)

    # Tampilkan confusion matrix jika tersedia
    for result in results:
        if 'Confusion Matrix' in result:
            st.subheader(f"Confusion Matrix - {result['Target']}")
            st.write(pd.DataFrame(result['Confusion Matrix'], columns=['Pred 0', 'Pred 1'], index=['True 0', 'True 1']))


    
# Langkah 8: Simulasi Skenario Masa Depan dengan Feature Engineering
st.header("8. Simulasi Skenario Masa Depan")
if 'data' in locals() and targets and features:
    st.write("Masukkan skenario masa depan untuk variabel independen:")

    # Membuat dataframe hanya untuk driver variables
    driver_variables = [
        "Harga_Minyak_Dunia-M", "Harga Batu Bara", "Fed Rate", "Freight Index", 
        "Upah Minimum", "USD-RP", "IND_GDP_K", "IND Interest Rate", "Core Inflation"
    ]
    future_data = pd.DataFrame({"Variable": driver_variables, "Nilai": [data[feature].mean() for feature in driver_variables]})

    # Konfigurasi tabel editable menggunakan AgGrid
    gb = GridOptionsBuilder.from_dataframe(future_data)
    gb.configure_default_column(editable=True)
    grid_options = gb.build()

    grid_response = AgGrid(future_data, gridOptions=grid_options, update_mode="MODEL_CHANGED", height=300, fit_columns_on_grid_load=True)

    # Mengambil data yang telah diedit oleh pengguna
    edited_future_data = pd.DataFrame(grid_response['data'])

    # Tambahkan fitur interaksi untuk input prediksi
    interaction_variables = ['USD-RP', 'Harga Batu Bara', 'Fed Rate']
    for interaction_var in interaction_variables:
        if interaction_var in edited_future_data['Variable'].values:
            interaction_value = edited_future_data.loc[edited_future_data['Variable'] == interaction_var, 'Nilai'].values[0]
            for feature in driver_variables:
                if feature != interaction_var:
                    interaction_feature = f"{feature}_x_{interaction_var}"
                    new_row = pd.DataFrame({"Variable": [interaction_feature], "Nilai": [interaction_value * edited_future_data.loc[edited_future_data['Variable'] == feature, 'Nilai'].values[0]]})
                    edited_future_data = pd.concat([edited_future_data, new_row], ignore_index=True)

    # Simpan hasil simulasi
    if 'simulation_results' not in st.session_state:
        st.session_state.simulation_results = []

    # Tombol untuk memulai prediksi
    st.header("9. Prediksi")
    if st.button("Mulai Prediksi"):
        # Konversi baseline ke format prediksi
        baseline_data = pd.DataFrame([future_data.set_index("Variable").T.iloc[0]])

        # Pastikan baseline_data memiliki fitur yang sama dengan X_train
        for feature in X_train.columns:
            if feature not in baseline_data.columns:
                baseline_data[feature] = 0
        baseline_data = baseline_data[X_train.columns]

        # Prediksi baseline
        baseline_predictions = []
        for target in targets:
            baseline_value = models[target].predict(baseline_data)[0]
            baseline_predictions.append({"Variable": target, "Baseline": baseline_value})

        # Konversi input data ke format prediksi
        input_data = pd.DataFrame([edited_future_data.set_index("Variable").T.iloc[0]])

        # Pastikan input_data memiliki fitur yang sama dengan X_train
        for feature in X_train.columns:
            if feature not in input_data.columns:
                input_data[feature] = 0
        input_data = input_data[X_train.columns]

        # Prediksi dengan driver yang diedit
        edited_predictions = []
        for target in targets:
            pred_value = models[target].predict(input_data)[0]
            edited_predictions.append({"Variable": target, "Edited Prediction": pred_value})

        # Gabungkan hasil baseline dan edited predictions
        comparison_table = pd.DataFrame(baseline_predictions).merge(pd.DataFrame(edited_predictions), on="Variable")

        # Simpan hasil simulasi
        st.session_state.simulation_results.append({
            "Updated Drivers": edited_future_data.set_index("Variable").T.to_dict(orient="records")[0],
            "Comparison Table": comparison_table

        })

    # Tampilkan semua hasil simulasi sebelumnya
    if st.session_state.simulation_results:
        # Tampilkan tabel variabel driver yang diedit setiap simulasi
        st.write("Hasil Semua Simulasi - Edited Drivers:")
        edited_drivers_tables = []
        for i, sim in enumerate(st.session_state.simulation_results):
            updated_drivers = pd.DataFrame([sim["Updated Drivers"]]).T
            updated_drivers.columns = [f"Simulasi {i + 1}"]
            edited_drivers_tables.append(updated_drivers)
        final_edited_drivers_table = pd.concat(edited_drivers_tables, axis=1)
        st.write(final_edited_drivers_table)

        st.write("Hasil Semua Simulasi - Predictions:")
        prediction_tables = []
        baseline_column = None
        for i, sim in enumerate(st.session_state.simulation_results):
            comparison_table = sim["Comparison Table"]
            if i == 0:  # Use Baseline column only from the first simulation
                baseline_column = comparison_table[["Variable", "Baseline"]]
                baseline_column.columns = ["Dependent Variable", "Baseline"]
            edited_prediction_column = comparison_table[["Variable", "Edited Prediction"]]
            edited_prediction_column.columns = ["Dependent Variable", f"Simulasi {i + 1} - Edited Prediction"]
            prediction_tables.append(edited_prediction_column.set_index("Dependent Variable"))
        final_prediction_table = pd.concat([baseline_column.set_index("Dependent Variable")] + prediction_tables, axis=1)
        st.write(final_prediction_table.to_html(escape=False, index=True), unsafe_allow_html=True)
