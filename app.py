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

# Input data standar dalam bentuk tabel
num_std = st.number_input("Jumlah data standar", min_value=3, max_value=20, value=6)

default_data = [{"Konsentrasi (ppm)": "", "Absorbansi": ""} for _ in range(num_std)]
edited_data = st.data_editor(
    pd.DataFrame(default_data),
    num_rows="dynamic",
    key="data_editor",
    use_container_width=True
)

# Parsing angka
std_data = []
for row in edited_data.itertuples(index=False):
    try:
        conc = float(row._0)
        absb = float(row._1)
        std_data.append((conc, absb))
    except:
        pass

df = pd.DataFrame(std_data, columns=["Konsentrasi", "Absorbansi"])

# Validasi input
if df.shape[0] < num_std:
    st.warning("Isi semua nilai terlebih dahulu dengan format angka yang benar.")
    st.stop()

if df["Konsentrasi"].nunique() < 2:
    st.error("Minimal dua nilai konsentrasi harus berbeda untuk menghitung regresi linier.")
    st.stop()

# Hitung regresi linier
a, b, r_value, _, _ = linregress(df["Konsentrasi"], df["Absorbansi"])
r_squared = r_value**2

if abs(a) < 1e-6:
    st.error("Slope terlalu kecil. Data mungkin tidak cukup bervariasi atau tidak linier.")
    st.stop()

# Plot kurva kalibrasi
fig, ax = plt.subplots(figsize=(5, 3))  # ukuran lebih kecil
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

# Tampilkan parameter regresi
st.markdown("### 📌 Parameter Regresi")
st.write(f"- Slope (a = ε·l): {a:.4f}")
st.write(f"- Intersep (b): {b:.4f}")
st.write(f"- Koefisien Korelasi (r): {r_value:.4f}")
st.write(f"- R-squared: {r_squared:.4f}")

# Interpretasi hasil
st.markdown("### 📖 Interpretasi")
if a > 0:
    st.write(f"✅ **Slope (a)** positif ({a:.4f}) menunjukkan hubungan linier positif: konsentrasi meningkat, absorbansi meningkat.")
else:
    st.write(f"⚠️ **Slope (a)** negatif ({a:.4f}) tidak umum pada metode ini — kemungkinan ada masalah data atau pengukuran.")

if abs(b) < 0.05:
    st.write(f"✅ **Intersep (b)** kecil ({b:.4f}) menunjukkan garis hampir melewati titik nol, sesuai teori Beer's Law.")
else:
    st.write(f"ℹ️ **Intersep (b)** ({b:.4f}) agak besar, mungkin ada error sistematis (misalnya blank tidak nol).")

if r_value > 0.995:
    st.write(f"✅ **Koefisien Korelasi (r)** sangat tinggi ({r_value:.4f}) — hubungan linier sangat baik.")
elif r_value > 0.98:
    st.write(f"⚠️ **Koefisien Korelasi (r)** cukup baik ({r_value:.4f}) — masih dalam batas wajar.")
else:
    st.write(f"❌ **Koefisien Korelasi (r)** rendah ({r_value:.4f}) — kemungkinan ada kesalahan data atau variasi besar.")

# Input sampel
st.markdown("---")
st.markdown("### 🧪 Hitung Konsentrasi Sampel")
num_samples = st.number_input("Jumlah sampel", min_value=1, max_value=10, value=6)

sample_results = []
st.markdown("#### Hasil Perhitungan Konsentrasi:")
cols = st.columns(min(6, num_samples))

conc_values = []
abs_values = []
for i in range(num_samples):
    with cols[i % 6]:
        abs_val_str = st.text_input(f"Absorbansi S{i+1}", key=f"s{i}")
        try:
            abs_val = float(abs_val_str)
        except:
            abs_val = 0.0
        abs_values.append(abs_val)
        conc_val = (abs_val - b) / a if a != 0 else 0
        conc_val = max(conc_val, 0)
        st.metric(label=f"Konsentrasi S{i+1}", value=f"{conc_val:.3f} ppm")
        conc_values.append(conc_val)

avg_conc_values = np.mean(conc_values)

selisih_values = []
for i in range(num_samples):
    selisih = math.fabs(conc_values[i] - avg_conc_values)
    rpd = selisih / avg_conc_values * 100
    selisih_values.append(selisih * selisih)
    sample_results.append({
        "Sampel": f"S{i+1}",
        "Absorbansi": f"{abs_values[i]:.4f}",
        "Konsentrasi (ppm)": f"{conc_values[i]:.3f}",
        "Selisih dengan Rata2": f"{selisih:.3f}",
        "RPD": f"{rpd:.3f}%"
    })

rsd = math.sqrt(np.mean(selisih_values))

# Tampilkan tabel hasil
if sample_results:
    st.markdown("#### 📋 Tabel Hasil:")
    st.table(pd.DataFrame(sample_results))
    st.markdown(f"📌 Rata-rata: {avg_conc_values:.2f}")
    st.markdown(f"📌 %RSD = {rsd:.2f}")

    # CV Horwitz
    st.markdown("#### 📉 Evaluasi Presisi (CV Horwitz)")
    horwitz_results = []
    horwitz_values = []

    for s in sample_results:
        ppm = float(s["Konsentrasi (ppm)"])
        C_decimal = ppm / 1000000
        if C_decimal > 0:
            cv_horwitz = 2 ** (1 - 0.5 * np.log10(C_decimal))
            horwitz_values.append(cv_horwitz)
        else:
            cv_horwitz = np.nan
        horwitz_results.append({
            "Sampel": s["Sampel"],
            "Konsentrasi (ppm)": f"{ppm:.3f}",
            "CV Horwitz (%)": f"{cv_horwitz:.2f}" if not np.isnan(cv_horwitz) else "NaN"
        })

    st.table(pd.DataFrame(horwitz_results))

    horwitz_values_clean = [v for v in horwitz_values if not np.isnan(v)]
    if horwitz_values_clean:
        avg_cv_horwitz = np.mean(horwitz_values_clean)
        st.markdown(f"📌 Rata-rata CV Horwitz: {avg_cv_horwitz:.2f}%")
