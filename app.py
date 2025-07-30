import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy.stats import linregress

st.set_page_config(page_title="Spektrofotometri Sederhana", layout="wide")
st.title("📊 Analisis Spektrofotometri - Beer's Law")

st.markdown("Masukkan minimal 3 data standar (konsentrasi dan absorbansi):")
st.markdown("🔔 **Catatan:** Gunakan tanda titik (.) untuk mengganti tanda koma (,) dalam penulisan angka desimal.")

# Input data standar
num_std = st.number_input("Jumlah data standar", min_value=3, max_value=20, value=6)

default_data = [{"Konsentrasi (ppm)": "", "Absorbansi": ""} for _ in range(num_std)]
edited_data = st.data_editor(
    pd.DataFrame(default_data),
    num_rows="dynamic",
    key="data_editor",
    use_container_width=True
)

# Parsing angka standar
std_data = []
for i in range(len(edited_data)):
    try:
        conc = float(edited_data.iloc[i]["Konsentrasi (ppm)"])
        absb = float(edited_data.iloc[i]["Absorbansi"])
        std_data.append((conc, absb))
    except:
        pass

df = pd.DataFrame(std_data, columns=["Konsentrasi", "Absorbansi"])

if df.shape[0] < num_std:
    st.warning("Isi semua nilai terlebih dahulu dengan format angka yang benar.")
    st.stop()

if df["Konsentrasi"].nunique() < 2:
    st.error("Minimal dua nilai konsentrasi harus berbeda untuk menghitung regresi linier.")
    st.stop()

# Regresi linier
a, b, r_value, _, _ = linregress(df["Konsentrasi"], df["Absorbansi"])
r_squared = r_value**2

if abs(a) < 1e-6:
    st.error("Slope terlalu kecil. Data mungkin tidak cukup bervariasi atau tidak linier.")
    st.stop()

# Plot kurva lebih kecil
fig, ax = plt.subplots(figsize=(4, 2.5))
x_fit = np.linspace(0, df["Konsentrasi"].max() * 1.1, 100)
y_fit = a * x_fit + b

ax.scatter(df["Konsentrasi"], df["Absorbansi"], label="Data Standar", color="blue")
ax.plot(x_fit, y_fit, color="red", linestyle="--", label=f"y = {a:.3f}x + {b:.3f}")
ax.set_xlabel("Konsentrasi (ppm)")
ax.set_ylabel("Absorbansi")
ax.set_title("Kurva Kalibrasi")
ax.grid(True)
ax.legend()

st.pyplot(fig)

# Parameter regresi
st.markdown("### 📌 Parameter Regresi")
st.write(f"- Slope (a = ε·l): {a:.4f}")
st.write(f"- Intersep (b): {b:.4f}")
st.write(f"- Koefisien Korelasi (r): {r_value:.4f}")
st.write(f"- R-squared: {r_squared:.4f}")

# Interpretasi
st.markdown("### 📖 Interpretasi")
if a > 0:
    st.write(f"✅ **Slope (a)** positif ({a:.4f}) menunjukkan hubungan linier positif.")
else:
    st.write(f"⚠️ **Slope (a)** negatif ({a:.4f}) — kemungkinan masalah data.")

if abs(b) < 0.05:
    st.write(f"✅ **Intersep (b)** kecil ({b:.4f}) sesuai teori Beer's Law.")
else:
    st.write(f"ℹ️ **Intersep (b)** ({b:.4f}) mungkin ada error sistematis.")

if r_value > 0.995:
    st.write(f"✅ **Koefisien Korelasi (r)** sangat tinggi ({r_value:.4f}).")
elif r_value > 0.98:
    st.write(f"⚠️ **Koefisien Korelasi (r)** cukup baik ({r_value:.4f}).")
else:
    st.write(f"❌ **Koefisien Korelasi (r)** rendah ({r_value:.4f}).")

# Input sampel via tabel
st.markdown("---")
st.markdown("### 🧪 Hitung Konsentrasi Sampel")
num_samples = st.number_input("Jumlah sampel", min_value=1, max_value=10, value=6)

# Tabel input hanya absorbansi
sample_data = pd.DataFrame({"Absorbansi": ["" for _ in range(num_samples)]})

edited_samples = st.data_editor(sample_data, num_rows="dynamic", key="samples_editor", use_container_width=True)

# Hitung otomatis konsentrasi
df_samples = edited_samples.copy()
conc_values = []
abs_values = []
for i in range(len(df_samples)):
    try:
        abs_val = float(df_samples.loc[i, "Absorbansi"])
        conc_val = (abs_val - b) / a if a != 0 else 0
        conc_val = max(conc_val, 0)
        df_samples.loc[i, "Konsentrasi (ppm)"] = round(conc_val, 3)
        abs_values.append(abs_val)
        conc_values.append(conc_val)
    except:
        df_samples.loc[i, "Konsentrasi (ppm)"] = ""

st.markdown("#### 📋 Tabel Hasil Sampel")
st.table(df_samples)

# Hitung RSD dan Horwitz jika data valid
if conc_values:
    avg_conc_values = np.mean(conc_values)
    selisih_values = [(x - avg_conc_values)**2 for x in conc_values]
    rsd = math.sqrt(np.mean(selisih_values))
    st.markdown(f"📌 Rata-rata: {avg_conc_values:.2f}")
    st.markdown(f"📌 %RSD = {rsd:.2f}")

    st.markdown("#### 📉 Evaluasi Presisi (CV Horwitz)")
    horwitz_results = []
    horwitz_values = []

    for idx, conc in enumerate(conc_values):
        C_decimal = conc / 1000000
        if C_decimal > 0:
            cv_horwitz = 2 ** (1 - 0.5 * np.log10(C_decimal))
            horwitz_values.append(cv_horwitz)
        else:
            cv_horwitz = np.nan
        horwitz_results.append({
            "Sampel": f"S{idx+1}",
            "Konsentrasi (ppm)": f"{conc:.3f}",
            "CV Horwitz (%)": f"{cv_horwitz:.2f}" if not np.isnan(cv_horwitz) else "NaN"
        })

    st.table(pd.DataFrame(horwitz_results))

    horwitz_values_clean = [v for v in horwitz_values if not np.isnan(v)]
    if horwitz_values_clean:
        avg_cv_horwitz = np.mean(horwitz_values_clean)
        st.markdown(f"📌 Rata-rata CV Horwitz: {avg_cv_horwitz:.2f}%")

