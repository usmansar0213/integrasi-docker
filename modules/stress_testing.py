import os
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from st_aggrid import AgGrid, GridOptionsBuilder
from modules.utils import get_user_file


def load_logo_and_title():
    col1, col2 = st.columns([1, 10])
    logo_path = os.path.join("static", "via_icon.jpg")
    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
            st.warning("Logo tidak ditemukan di folder static/")
    with col2:
        st.title("Stress Testing")


def load_dataset(uploaded_file, default_file_path=None):
    data = None
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                data = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                data = pd.read_excel(uploaded_file)
            st.write("Dataset yang diunggah:")
            st.write(data.head())
        except Exception as e:
            st.error(f"Gagal memuat dataset. Error: {e}")
    elif default_file_path:
        try:
            data = pd.read_excel(default_file_path)
            st.write(f"Dataset default dari: {default_file_path}")
            st.write(data.head())
        except Exception as e:
            st.error(f"Gagal memuat dataset default. Error: {e}")
    return data
def find_tahun_column(data):
    """
    Mencari kolom 'tahun' atau 'year' secara fleksibel (tanpa memperhatikan kapital dan spasi).
    """
    tahun_aliases = ['tahun', 'year']
    normalized_columns = data.columns.str.strip().str.lower()
    for col in normalized_columns:
        if col in tahun_aliases:
            # Ambil nama kolom aslinya (case-sensitive)
            return data.columns[normalized_columns == col][0]
    return None

def handle_outliers(data):
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
    return data
def select_variables(data):
    all_columns = data.columns.tolist()
    targets = st.multiselect("Pilih variabel dependen (target):", all_columns)
    
    features = st.multiselect(
        "Pilih variabel independen (fitur):", 
        all_columns, 
        default=all_columns
    )

    # Hindari fitur duplikat dari target
    for target in targets:
        if target in features:
            features.remove(target)

    return features, targets


def split_and_engineer_features(data, features, targets, interaction_variables):
    test_size = st.slider("Pilih ukuran data uji (%):", 10, 50, 20, key="test_size")
    
    X = data[features].copy()
    y = data[targets].copy()

    for interaction_var in interaction_variables:
        if interaction_var in features:
            for feature in features:
                if feature != interaction_var:
                    interaction_feature = f"{feature}_x_{interaction_var}"
                    X[interaction_feature] = X[feature] * X[interaction_var]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size/100, random_state=42
    )

    return X, X_train, X_test, y_train, y_test

def train_models(X_train, y_train, targets):
    n_estimators = st.slider("Pilih jumlah pohon dalam hutan:", 10, 200, 100)
    max_depth = st.slider("Pilih kedalaman maksimum pohon:", 1, 20, 10)
    
    models = {}
    for target in targets:
        model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
        model.fit(X_train, y_train[target])
        models[target] = model

    st.success("Model telah dilatih untuk semua variabel dependen.")
    return models


def validate_models(models, X_test, y_test, targets):
    results = []
    for target in targets:
        y_pred = models[target].predict(X_test)
        mse = mean_squared_error(y_test[target], y_pred)
        r2 = r2_score(y_test[target], y_pred)
        results.append({"Target": target, "MSE": mse, "R²": r2})

    results_df = pd.DataFrame(results)

    def color_cells(val, column):
        if column == 'R²':
            return 'background-color: lightgreen' if val >= 0.7 else 'background-color: yellow'
        elif column == 'MSE':
            return 'background-color: lightgreen' if val < 10 else 'background-color: yellow'
        return ''

    styled_results_df = results_df.style.applymap(lambda x: color_cells(x, 'MSE') if isinstance(x, (float, int)) else '', subset=['MSE'])
    styled_results_df = styled_results_df.applymap(lambda x: color_cells(x, 'R²') if isinstance(x, (float, int)) else '', subset=['R²'])

    st.write("Hasil Validasi:")
    st.write(styled_results_df.to_html(escape=False, index=False), unsafe_allow_html=True)



def run_scenario_simulation_with_user_inputs(data, models, X_train, targets, features, tahun_col):


    st.header("8. Simulasi Skenario Masa Depan - Multi Skenario")
    all_numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    driver_variables = [col for col in all_numeric_cols if col != tahun_col]



    base_values = {var: data[var].mean() if var in data.columns else 0 for var in driver_variables}
    future_data = pd.DataFrame({
        "Variable": driver_variables,
        "Pesimistis": [base_values[v] for v in driver_variables],
        "Moderat": [base_values[v] for v in driver_variables],
        "Optimistis": [base_values[v] for v in driver_variables],
    })

    gb = GridOptionsBuilder.from_dataframe(future_data)
    gb.configure_default_column(editable=True)
    grid_options = gb.build()
    grid_response = AgGrid(future_data, gridOptions=grid_options, update_mode="MODEL_CHANGED", height=400, fit_columns_on_grid_load=True)
    edited_df = pd.DataFrame(grid_response['data'])

    scenario_inputs = {}
    for scenario in ['Pesimistis', 'Moderat', 'Optimistis']:
        df = pd.DataFrame({"Variable": edited_df["Variable"], "Nilai": edited_df[scenario]})
        interaction_vars = [var for var in features if var in data.columns]
        interaction_rows = []
        for interaction_var in interaction_vars:
            if interaction_var in df["Variable"].values:
                interaction_val = df[df["Variable"] == interaction_var]["Nilai"].values[0]
                for base_var in driver_variables:
                    if base_var != interaction_var and base_var in df["Variable"].values:
                        base_val = df[df["Variable"] == base_var]["Nilai"].values[0]
                        interaction_feature = f"{base_var}_x_{interaction_var}"
                        interaction_rows.append({"Variable": interaction_feature, "Nilai": base_val * interaction_val})
        df = pd.concat([df, pd.DataFrame(interaction_rows)], ignore_index=True)
        scenario_inputs[scenario] = df
    return scenario_inputs


def display_simulation_results_with_training_forecast_chart(
    scenario_inputs, models, X_train, y_train, targets, tahun_terakhir, tahun_prediksi_akhir
):
    st.header("9. Grafik Gabungan Aktual vs Prediksi (Training) dan Prediksi Masa Depan")

    tahun_terakhir = int(tahun_terakhir)
    tahun_prediksi_akhir = int(tahun_prediksi_akhir)
    tahun_prediksi_range = list(range(tahun_terakhir + 1, tahun_prediksi_akhir + 1))

    # Hitung prediksi masa depan
    predictions = {}
    for scenario_name, df in scenario_inputs.items():
        input_data = pd.DataFrame([df.set_index("Variable").T.iloc[0]])
        for feature in X_train.columns:
            if feature not in input_data.columns:
                input_data[feature] = 0
        input_data = input_data[X_train.columns]

        scenario_result = {}
        for target in targets:
            scenario_result[target] = models[target].predict(input_data)[0]
        predictions[scenario_name] = scenario_result

    for target in targets:
        fig, ax = plt.subplots(figsize=(10, 4))

        # Data aktual
        y_actual = y_train[target].reset_index(drop=True)
        tahun_training = list(range(tahun_terakhir - len(y_actual) + 1, tahun_terakhir + 1))
        ax.plot(tahun_training, y_actual, label="Aktual", linewidth=2, color="blue")

        # Prediksi terhadap data training
        y_pred_train = models[target].predict(X_train)
        ax.plot(tahun_training, y_pred_train, label="Prediksi Training", linewidth=2, color="purple", linestyle='--')

        # Prediksi skenario ke masa depan
        scenario_colors = {
            'Pesimistis': 'red',
            'Moderat': 'orange',
            'Optimistis': 'green'
        }

        for scenario_name in ['Pesimistis', 'Moderat', 'Optimistis']:
            pred_value = predictions[scenario_name][target]
            nilai_flat = [pred_value] * len(tahun_prediksi_range)
            ax.plot(
                tahun_prediksi_range, nilai_flat,
                label=scenario_name,
                color=scenario_colors[scenario_name],
                linestyle='--', marker='o'
            )

        ax.set_title(f"{target}")
        ax.set_xlabel("Tahun")
        ax.set_ylabel("Nilai")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)
        
    # Buat DataFrame dari hasil prediksi semua skenario dan tahun
    data_prediksi = []
    for scenario_name, hasil in predictions.items():
        for tahun in tahun_prediksi_range:
            row = {"Tahun": tahun, "Skenario": scenario_name}
            row.update(hasil)
            data_prediksi.append(row)

    pivot_table = pd.DataFrame(data_prediksi)

    # Format tahun agar lebih rapi (tanpa .00)
    pivot_table["Tahun"] = pivot_table["Tahun"].astype(int)
    pivot_table = pivot_table.sort_values(by=["Tahun", "Skenario"]).reset_index(drop=True)

    # Pilihan interaktif filter
    tahun_terpilih = st.multiselect(
        "📆 Pilih Tahun:", options=pivot_table["Tahun"].unique().tolist(), default=pivot_table["Tahun"].unique().tolist()
    )
    skenario_terpilih = st.multiselect(
        "📊 Pilih Skenario:", options=pivot_table["Skenario"].unique().tolist(), default=pivot_table["Skenario"].unique().tolist()
    )

    # Filter data
    filtered = pivot_table[
        pivot_table["Tahun"].isin(tahun_terpilih) &
        pivot_table["Skenario"].isin(skenario_terpilih)
    ]

    # Format hanya kolom numerik
    numeric_cols = filtered.select_dtypes(include=[float, int]).columns.difference(["Tahun"])
    st.subheader("📋 Tabel Ringkasan Prediksi")
    st.dataframe(filtered.style.format({col: "{:.2f}" for col in numeric_cols}))

    return pivot_table



def export_predictions_to_excel(pivot_table):
    buffer = io.BytesIO()
    pivot_table.to_excel(buffer, index=False)
    st.download_button(
        label="📥 Unduh Hasil Prediksi (Excel)",
        data=buffer.getvalue(),
        file_name="prediksi_stress_testing.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def display_feature_importance(models, X_train, targets):
    st.header("10. Bobot Pengaruh Variabel")

    # Kumpulkan importance untuk semua target
    importance_summary = []

    for target in targets:
        model = models[target]
        importances = model.feature_importances_
        features = X_train.columns

        df_imp = pd.DataFrame({
            "Fitur": features,
            "Importance": importances
        }).sort_values(by="Importance", ascending=False).reset_index(drop=True)
        df_imp["Target"] = target
        importance_summary.append(df_imp)

        # Tampilkan chart per target
        st.subheader(f"🎯 Target: {target}")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(df_imp["Fitur"], df_imp["Importance"], color='skyblue')
        ax.invert_yaxis()
        ax.set_xlabel("Bobot Pengaruh (%)")
        ax.set_title(f"Feature Importance - {target}")
        st.pyplot(fig)

    # Gabungkan ke satu tabel untuk tampilan global
    df_all = pd.concat(importance_summary, ignore_index=True)
    df_all["Importance"] = df_all["Importance"] * 100  # Ubah ke persen

    st.subheader("📊 Tabel Bobot Pengaruh Semua Target")
    st.dataframe(
        df_all.sort_values(by=["Target", "Importance"], ascending=[True, False])
        .style.format({"Importance": "{:.2f} %"})
    )

    return df_all

def main():
    load_logo_and_title()

    st.header("1. Memuat Dataset")
    uploaded_file = st.file_uploader("Unggah file Excel atau CSV Anda", type=["csv", "xlsx"])
    default_file_path = None  # Ganti jika ingin gunakan file default
    data = load_dataset(uploaded_file, default_file_path)

    # Validasi wajib: kolom Tahun/Year harus ada
    if data is not None:
        # Hilangkan spasi di awal/akhir kolom
        data.columns = data.columns.str.strip()
        
        # Cari kolom 'Tahun' atau 'Year' secara fleksibel
        tahun_aliases = ['tahun', 'year']
        normalized_columns = data.columns.str.lower()
        tahun_col = None
        for col in normalized_columns:
            if col in tahun_aliases:
                tahun_col = data.columns[normalized_columns == col][0]
                break

        if tahun_col is None:
            st.error("Dataset wajib memiliki kolom 'Tahun' atau 'Year'.")
            return

        st.header("2. Penanganan Outlier")
        data = handle_outliers(data)

        st.header("3. Pemilihan Variabel")
        features, targets = select_variables(data)

        if features and targets:
            st.header("4. Data History")
            interaction_vars = [f for f in features if f in data.columns]
            X, X_train, X_test, y_train, y_test = split_and_engineer_features(data, features, targets, interaction_vars)
            st.write("Data history yang digunakan untuk pelatihan:")
            st.write(X_train.head())

            st.header("5. Data Interaction Variables")
            interaction_columns = [col for col in X.columns if '_x_' in col]
            if interaction_columns:
                st.write(X[interaction_columns].head())
            else:
                st.write("Tidak ada fitur interaksi yang dihasilkan.")

            st.header("6. Pelatihan Model Random Forest")
            models = train_models(X_train, y_train, targets)

            st.header("7. Validasi Model")
            validate_models(models, X_test, y_test, targets)


            scenario_inputs = run_scenario_simulation_with_user_inputs(data, models, X_train, targets, features, tahun_col)

            tahun_prediksi_akhir = st.number_input(
                "Prediksi hingga tahun:",
                min_value=2024,
                max_value=2100,
                value=2025
            )
            tahun_terakhir = data[tahun_col].max()

            pivot_table = display_simulation_results_with_training_forecast_chart(
                scenario_inputs, models, X_train, y_train, targets, tahun_terakhir, tahun_prediksi_akhir
            )

            display_feature_importance(models, X_train, targets)

            st.header("10. Unduh Hasil Prediksi")
            export_predictions_to_excel(pivot_table)
