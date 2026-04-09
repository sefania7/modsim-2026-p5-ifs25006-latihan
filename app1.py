# =====================================================================
# MONTE CARLO SIMULATION
# Estimasi Durasi Pembangunan Gedung FITE 5 Lantai
# Praktikum MODSIM
# =====================================================================

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

# =====================================================================
# CONFIG PAGE
# =====================================================================

st.set_page_config(
    page_title="Simulasi Monte Carlo Gedung FITE",
    page_icon="📐",
    layout="wide"
)

st.title("Simulasi Monte Carlo")
st.subheader("Estimasi Waktu Pembangunan Gedung FITE 5 Lantai")

# =====================================================================
# DATA TAHAPAN PROYEK
# =====================================================================

TAHAPAN = {
    "Perencanaan": (1.5, 2.5, 4),
    "Persiapan Lahan": (1, 1.5, 3),
    "Struktur Bangunan": (4, 6, 9),
    "Instalasi MEP": (2, 3, 5),
    "Lab Komputer": (1, 1.5, 2.5),
    "Lab VR": (1.5, 2.5, 4.5),
    "Lab Mobile": (0.5, 1, 1.8),
    "Finishing": (1.5, 2.5, 4),
    "Testing": (0.5, 1, 2),
    "Serah Terima": (0.5, 0.8, 1.5)
}

# =====================================================================
# SIDEBAR INPUT
# =====================================================================

st.sidebar.header("Parameter Simulasi")

n_sim = st.sidebar.slider(
    "Jumlah Iterasi",
    1000,
    50000,
    20000
)

seed = st.sidebar.number_input(
    "Random Seed",
    0,
    9999,
    42
)

np.random.seed(seed)

# =====================================================================
# FUNGSI DISTRIBUSI PERT
# =====================================================================

def pert_sample(opt, ml, pes, size):

    mean = (opt + 4 * ml + pes) / 6
    std = (pes - opt) / 6

    a = (mean - opt) / (pes - opt)
    b = (pes - mean) / (pes - opt)

    alpha = 1 + 4 * a
    beta = 1 + 4 * b

    return opt + np.random.beta(alpha, beta, size) * (pes - opt)


# =====================================================================
# SIMULASI MONTE CARLO
# =====================================================================

if st.button("Jalankan Simulasi"):

    data = {}

    for stage, param in TAHAPAN.items():

        opt, ml, pes = param

        data[stage] = pert_sample(
            opt,
            ml,
            pes,
            n_sim
        )

    df = pd.DataFrame(data)

    df["Total"] = df.sum(axis=1)

    total = df["Total"]

# =====================================================================
# STATISTIK
# =====================================================================

    mean = total.mean()
    median = total.median()
    std = total.std()

    ci80 = np.percentile(total, [10, 90])
    ci95 = np.percentile(total, [2.5, 97.5])

# =====================================================================
# METRICS
# =====================================================================

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Rata-rata", f"{mean:.2f} bulan")
    col2.metric("Median", f"{median:.2f} bulan")
    col3.metric("Std Dev", f"{std:.2f}")
    col4.metric("CI 80%", f"{ci80[0]:.1f}-{ci80[1]:.1f}")
    col5.metric("CI 95%", f"{ci95[0]:.1f}-{ci95[1]:.1f}")

# =====================================================================
# HISTOGRAM DISTRIBUSI
# =====================================================================

    kde = stats.gaussian_kde(total)

    x = np.linspace(total.min(), total.max(), 400)

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=total,
            nbinsx=60,
            histnorm="probability density",
            name="Histogram"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=kde(x),
            mode="lines",
            name="KDE"
        )
    )

    fig.add_vrect(
        x0=ci95[0],
        x1=ci95[1],
        fillcolor="red",
        opacity=0.1,
        line_width=0,
        annotation_text="95% CI"
    )

    fig.add_vrect(
        x0=ci80[0],
        x1=ci80[1],
        fillcolor="blue",
        opacity=0.1,
        line_width=0,
        annotation_text="80% CI"
    )

    fig.update_layout(
        title="Distribusi Durasi Proyek",
        xaxis_title="Durasi (bulan)",
        yaxis_title="Density"
    )

    st.plotly_chart(fig, use_container_width=True)

# =====================================================================
# PROBABILITAS DEADLINE
# =====================================================================

    st.subheader("Probabilitas Deadline")

    deadlines = [16, 18, 20, 22, 24]

    prob = []

    for d in deadlines:
        prob.append(np.mean(total <= d) * 100)

    prob_df = pd.DataFrame({
        "Deadline": deadlines,
        "Probability (%)": prob
    })

    st.dataframe(prob_df)

# =====================================================================
# CRITICAL PATH ANALYSIS
# =====================================================================

    st.subheader("Analisis Jalur Kritis")

    corr = {}

    for stage in TAHAPAN:

        corr_val = stats.spearmanr(
            df[stage],
            total
        )[0]

        corr[stage] = corr_val

    corr_df = pd.DataFrame({
        "Tahapan": list(corr.keys()),
        "Correlation": list(corr.values())
    })

    corr_df = corr_df.sort_values(
        "Correlation",
        ascending=False
    )

    st.dataframe(corr_df)

# =====================================================================
# KONTRIBUSI DURASI
# =====================================================================

    st.subheader("Kontribusi Durasi Tahapan")

    mean_stage = df.mean().drop("Total")

    contrib = mean_stage / mean * 100

    contrib_df = pd.DataFrame({
        "Tahapan": mean_stage.index,
        "Mean Durasi": mean_stage.values,
        "Kontribusi (%)": contrib.values
    })

    st.dataframe(contrib_df)

# =====================================================================
# BAR CHART KONTRIBUSI
# =====================================================================

    fig2 = go.Figure()

    fig2.add_trace(
        go.Bar(
            x=contrib_df["Tahapan"],
            y=contrib_df["Kontribusi (%)"]
        )
    )

    fig2.update_layout(
        title="Kontribusi Durasi Tahapan",
        xaxis_title="Tahapan",
        yaxis_title="% Durasi Proyek"
    )

    st.plotly_chart(fig2, use_container_width=True)