import streamlit as st
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.inspection import permutation_importance
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from main import get_user_file

# Judul Aplikasi
st.title("Prediksi Laba Usaha dengan Random Forest")

# 1. Unggah File Excel
st.header("1. Unggah File Excel")
uploaded_file = st.file_uploader("Unggah file Excel", type="xlsx")

# Inisialisasi session state
if "df" not in st.session_state:
    st.session_state.df = None
if "rf1_results" not in st.session_state:
    st.session_state.rf1_results = {}
if "rf2_results" not in st.session_state:
    st.session_state.rf2_results = {}
if "dependent_var" not in st.session_state:
    st.session_state.dependent_var = None
if "checkbox_states" not in st.session_state:
    st.session_state.checkbox_states = {}
if "scenario_data" not in st.session_state:
    st.session_state.scenario_data = {}

def evaluate_rf1_results():
    st.write("Hasil Random Forest Pertama:")
    st.write(f"Mean Squared Error (MSE): {st.session_state.rf1_results['mse']}")
    st.write(f"R-squared (R2): {st.session_state.rf1_results['r2']}")

    # Evaluasi hasil berdasarkan standar
    r2_threshold = 0.7
    mse_threshold = st.session_state.rf1_results['y_test'].var() * 0.1  # contoh standar MSE adalah 10% dari variansi

    if st.session_state.rf1_results['r2'] >= r2_threshold:
        st.success("Model memiliki performa yang baik berdasarkan nilai R-squared.")
    else:
        st.warning("Model mungkin perlu perbaikan karena nilai R-squared lebih rendah dari standar (0.7).")

    if st.session_state.rf1_results['mse'] <= mse_threshold:
        st.success("Mean Squared Error (MSE) berada dalam batas yang baik.")
    else:
        st.warning("Mean Squared Error (MSE) lebih tinggi dari batas yang diharapkan. Coba evaluasi ulang model atau data.")

def plot_importance():
    st.write("Permutation Importance:")
    fig, ax = plt.subplots()
    st.session_state.rf1_results['perm_importance_df'].plot(
        kind="barh", x="Feature", y="Importance", legend=False, ax=ax
    )
    ax.set_xlabel("Importance")
    ax.set_ylabel("Feature")
    ax.set_title("Permutation Importance")
    st.pyplot(fig)



def export_to_excel(df, filename):
    path = get_user_file(filename)
    df.to_excel(path, index=False)
    st.success(f"Hasil berhasil disimpan di: {path}")

if uploaded_file is not None:
    # 2. Baca dan Praproses Data
    st.header("2. Baca dan Praproses Data")
    if st.session_state.df is None:
        df = pd.read_excel(uploaded_file, sheet_name="Sheet1")

        # Sort dan format data
        df.sort_values(by="Year", inplace=True)
        df["Year"] = pd.to_datetime(df["Year"], format="%Y")
        df.set_index("Year", inplace=True)

        st.session_state.df = df
    else:
        df = st.session_state.df

    # Tampilkan data yang siap diproses
    st.write("Data yang siap diproses:")
    st.dataframe(df)

    # 3. Pilih Variabel Dependen
    st.header("3. Pilih Variabel Dependen")
    st.session_state.dependent_var = st.selectbox("Pilih variabel dependen:", options=df.columns)

    # Tentukan variabel independen
    independent_vars = [col for col in df.columns if col != st.session_state.dependent_var]

    # 4.  Random Forest Pertama
    st.header("4.  Random Forest Pertama")

    if st.button(" Random Forest Pertama"):
        X = df[independent_vars]
        y = df[st.session_state.dependent_var]

        # Bagi data menjadi data latih dan data uji
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Tambahkan bobot lebih tinggi untuk data yang lebih baru
        weights = np.linspace(1, 2, len(X_train))  # Bobot meningkat linier
        sample_weights = weights / weights.sum()  # Normalisasi bobot

        # Inisialisasi dan latih model Random Forest dengan bobot
        model = RandomForestRegressor(random_state=42)
        model.fit(X_train, y_train, sample_weight=sample_weights)

        # Prediksi pada data uji
        y_pred = model.predict(X_test)

        # Evaluasi model
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Permutation Importance
        perm_importance = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42)
        perm_importance_df = pd.DataFrame({
            "Feature": X_test.columns,
            "Importance": perm_importance.importances_mean
        })
        perm_importance_df.sort_values(by="Importance", ascending=False, inplace=True)

        # Simpan hasil Random Forest pertama di session state
        st.session_state.rf1_results = {
            "model": model,
            "mse": mse,
            "r2": r2,
            "perm_importance_df": perm_importance_df,
            "X_train": X_train,
            "y_test": y_test,
            "y_pred": y_pred
        }

    # Tampilkan hasil Random Forest pertama jika sudah ada
    if st.session_state.rf1_results:
        evaluate_rf1_results()
        plot_importance()

    # 5. Pilih Variabel untuk Random Forest Kedua
    st.header("5. Pilih Variabel untuk Random Forest Kedua")
    if st.session_state.rf1_results:
        perm_importance_df = st.session_state.rf1_results['perm_importance_df']
        columns = perm_importance_df["Feature"].tolist()

        # Otomatis menjadikan variabel dependen RF2 sama dengan RF1
        dependent_var_rf2 = st.session_state.dependent_var
        st.write(f"Variabel dependen untuk RF2: {dependent_var_rf2}")

        # Pilih variabel independen untuk model kedua menggunakan checkbox dalam 3 kolom
        independent_vars_rf2 = [col for col in columns if col != dependent_var_rf2]
        selected_independent_vars_rf2 = []
        st.write("Pilih variabel independen:")

        cols = st.columns(3)  # Buat 3 kolom untuk checkbox
        for idx, var in enumerate(independent_vars_rf2):
            col = cols[idx % 3]
            if var not in st.session_state.checkbox_states:
                st.session_state.checkbox_states[var] = False
            state = col.checkbox(var, value=st.session_state.checkbox_states[var])
            st.session_state.checkbox_states[var] = state
            if state:
                selected_independent_vars_rf2.append(var)

        # Tambahkan dependen variable ke tabel data variabel terpilih
        selected_data = df[[dependent_var_rf2] + selected_independent_vars_rf2]

        # 6. Skenario untuk Variabel Terpilih
        if selected_independent_vars_rf2:
            st.header("6. Skenario untuk Variabel Terpilih")

            years_to_predict = st.number_input("Masukkan jumlah tahun yang akan diprediksi:", min_value=0, step=1, value=0)
            st.session_state.years_to_predict = years_to_predict

            predictions = {"Year": []}

            if years_to_predict > 0:
                future_years = [df.index.year.max() + i for i in range(1, years_to_predict + 1)]
                predictions["Year"] = future_years
                for feature in selected_independent_vars_rf2:
                    x = np.array(df.index.year).reshape(-1, 1)
                    y = df[feature].values
                    coef = np.polyfit(x.flatten(), y, 1)
                    predictions[feature] = [np.polyval(coef, year) for year in future_years]

                # Prediksi dependen variabel
                dep_x = df.index.year
                dep_y = df[dependent_var_rf2]
                dep_coef = np.polyfit(dep_x, dep_y, 1)
                predictions[dependent_var_rf2] = [np.polyval(dep_coef, year) for year in future_years]

            prediction_df = pd.DataFrame(predictions)

            # Gabungkan tabel history dan prediksi
            history_df = df[[dependent_var_rf2] + selected_independent_vars_rf2].copy()
            history_df.index = history_df.index.year
            history_df.reset_index(inplace=True)
            history_df.rename(columns={'index': 'Year'}, inplace=True)

            if years_to_predict > 0:
                combined_df = pd.concat([history_df, prediction_df], axis=0, ignore_index=True)
            else:
                combined_df = history_df.copy()

            st.write("Tabel Gabungan History dan Prediksi (dapat diedit):")

            # Konfigurasikan AgGrid agar dapat diedit dengan ukuran kolom fleksibel
            gb = GridOptionsBuilder.from_dataframe(combined_df)
            gb.configure_default_column(editable=True, resizable=True, autoHeight=True, wrapText=True)
            gb.configure_grid_options(enableCellChangeFlash=True)
            grid_options = gb.build()

            grid_response = AgGrid(
                combined_df,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.VALUE_CHANGED,
                allow_unsafe_jscode=True,
                fit_columns_on_grid_load=False
            )

            edited_df = pd.DataFrame(grid_response['data'])

            # Tombol untuk menyimpan hasil edited_df ke session state
            if st.button("Simpan Hasil Tabel yang Diedit"):
                st.session_state.scenario_data = edited_df
                st.success("Hasil tabel yang diedit telah disimpan ke session state.")

            # Tampilkan edited_df yang disimpan
            if "scenario_data" in st.session_state:
                st.write("Data yang disimpan:")
                st.dataframe(st.session_state.scenario_data)

            # 7. Random Forest Kedua
            st.header("7. Random Forest Kedua")

            if st.button("Jalankan Random Forest Kedua"):
                if "scenario_data" in st.session_state:
                    scenario_df = st.session_state.scenario_data

                    # Set 'Year' column as index
                    if 'Year' in scenario_df.columns:
                        scenario_df = scenario_df.set_index('Year')

                    # Define independent and dependent variables
                    X_rf2 = scenario_df[selected_independent_vars_rf2]
                    y_rf2 = scenario_df[dependent_var_rf2]

                    # Split data into training and testing sets
                    X_train_rf2, X_test_rf2, y_train_rf2, y_test_rf2 = train_test_split(
                        X_rf2, y_rf2, test_size=0.2, random_state=42
                    )

                    # Add higher weights for newer data
                    weights = np.linspace(1, 2.1, len(X_train_rf2))  # Linear increasing weights with 10% increment
                    sample_weights = weights / weights.sum()  # Normalize weights

                    # Initialize and train Random Forest model with weights
                    model_rf2 = RandomForestRegressor(random_state=42)
                    model_rf2.fit(X_train_rf2, y_train_rf2, sample_weight=sample_weights)

                    # Predict and evaluate
                    y_pred_rf2 = model_rf2.predict(X_test_rf2)

                    mse_rf2 = mean_squared_error(y_test_rf2, y_pred_rf2)
                    r2_rf2 = r2_score(y_test_rf2, y_pred_rf2)

                    # Display results
                    st.write("Hasil Random Forest Kedua:")
                    st.write(f"Mean Squared Error (MSE): {mse_rf2}")
                    st.write(f"R-squared (R2): {r2_rf2}")

                    # Evaluasi hasil berdasarkan standar
                    r2_threshold = 0.7
                    mse_threshold = y_test_rf2.var() * 0.1  # contoh standar MSE adalah 10% dari variansi

                    if r2_rf2 >= r2_threshold:
                        st.success("Model memiliki performa yang baik berdasarkan nilai R-squared.")
                    else:
                        st.warning("Model mungkin perlu perbaikan karena nilai R-squared lebih rendah dari standar (0.7).")

                    if mse_rf2 <= mse_threshold:
                        st.success("Mean Squared Error (MSE) berada dalam batas yang baik.")
                    else:
                        st.warning("Mean Squared Error (MSE) lebih tinggi dari batas yang diharapkan. Coba evaluasi ulang model atau data.")

                    # Backtesting and Confusion Matrix
                    from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

                    st.write("Backtesting dan Evaluasi Confusion Matrix:")
                    y_test_rf2_class = (y_test_rf2 > y_test_rf2.median()).astype(int)
                    y_pred_rf2_class = (y_pred_rf2 > y_test_rf2.median()).astype(int)

                    cm = confusion_matrix(y_test_rf2_class, y_pred_rf2_class)
                    st.write("Confusion Matrix:")
                    st.dataframe(pd.DataFrame(cm, index=["Actual Negative", "Actual Positive"], columns=["Predicted Negative", "Predicted Positive"]))

                    # Evaluate confusion matrix performance
                    tn, fp, fn, tp = cm.ravel()
                    accuracy_threshold = 0.8
                    if (tp + tn) / cm.sum() >= accuracy_threshold:
                        st.success("Model memiliki performa yang baik berdasarkan nilai Accuracy.")
                    else:
                        st.warning("Model mungkin perlu perbaikan karena nilai Accuracy lebih rendah dari standar (0.8).")

                    fig, ax = plt.subplots()
                    ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Negative", "Positive"]).plot(ax=ax)
                    st.pyplot(fig)

                    # Permutation Importance
                    perm_importance = permutation_importance(model_rf2, X_test_rf2, y_test_rf2, random_state=42)
                    sorted_idx = perm_importance.importances_mean.argsort()

                    # Create a bar chart and table for permutation importance
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.barh(X_rf2.columns[sorted_idx], perm_importance.importances_mean[sorted_idx])
                    ax.set_title("Permutation Importance")
                    ax.set_xlabel("Mean Importance")

                    st.pyplot(fig)

                    # Display importance values in a table
                    importance_df = pd.DataFrame({
                        "Feature": X_rf2.columns[sorted_idx],
                        "Importance": perm_importance.importances_mean[sorted_idx]
                    }).sort_values(by="Importance", ascending=False)
                    st.write("Tabel Permutation Importance:")
                    st.dataframe(importance_df)

                    # Plot history vs predictions
                    fig, ax = plt.subplots()
                    years_test = y_test_rf2.index  # Extract years for the test set
                    ax.plot(years_test, y_test_rf2.values, label="Actual", marker='o')
                    ax.plot(years_test, y_pred_rf2, label="Prediction", marker='x')
                    ax.set_title("Actual vs Prediction")
                    ax.set_xlabel("Year")
                    ax.set_ylabel("Values")
                    ax.legend()

                    st.pyplot(fig)

                else:
                    st.write("Data skenario tidak ditemukan di session state.")
    if st.button("Ekspor Hasil ke Excel"):
        export_to_excel(st.session_state.scenario_data, "hasil_prediksi_rf2.xlsx")
