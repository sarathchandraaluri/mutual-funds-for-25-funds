import streamlit as st
import pandas as pd
import requests
import numpy as np
import plotly.express as px
from datetime import timedelta

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="MF Elite Dashboard",
    layout="wide",
    page_icon="📊"
)

# -----------------------------
# PREMIUM CSS
# -----------------------------
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: white;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #020617;
}

/* Cards */
.stMetric {
    background: rgba(255,255,255,0.05);
    padding: 15px;
    border-radius: 15px;
    backdrop-filter: blur(10px);
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #6366f1, #06b6d4);
    color: white;
    border-radius: 10px;
    border: none;
    transition: 0.3s;
}
.stButton>button:hover {
    transform: scale(1.05);
}

/* Inputs */
input, .stSelectbox, .stMultiSelect {
    background-color: #020617 !important;
    color: white !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    background-color: rgba(255,255,255,0.05);
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# TITLE
# -----------------------------
st.title("📊 Mutual Fund Elite Dashboard")

# -----------------------------
# CACHED DATA
# -----------------------------
@st.cache_data(ttl=3600)
def get_fund_list():
    try:
        res = requests.get("https://api.mfapi.in/mf", timeout=10)
        if res.status_code == 200:
            return pd.DataFrame(res.json()).head(200)
    except:
        pass

    return pd.DataFrame([
        {"schemeName": "Axis Bluechip Fund", "schemeCode": "120503"},
        {"schemeName": "HDFC Top 100 Fund", "schemeCode": "118989"},
        {"schemeName": "SBI Bluechip Fund", "schemeCode": "118834"},
    ])

@st.cache_data(ttl=3600)
def get_fund_data(code):
    try:
        url = f"https://api.mfapi.in/mf/{code}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json()
    except:
        return None

# -----------------------------
# LOAD DATA
# -----------------------------
fund_df = get_fund_list()

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("🔍 Filters")

search = st.sidebar.text_input("Search Fund")

filtered_df = fund_df.copy()

if search:
    filtered_df = filtered_df[
        filtered_df['schemeName'].str.contains(search, case=False, na=False)
    ]

selected_funds = st.multiselect(
    "Select Mutual Funds",
    filtered_df['schemeName']
)

timeframe = st.selectbox(
    "Timeframe",
    ["3 Months", "1 Year", "3 Years", "5 Years"]
)

# -----------------------------
# PROCESS
# -----------------------------
results = []

if selected_funds:

    with st.spinner("⚡ Analyzing funds..."):

        for fund in selected_funds:
            try:
                code = fund_df[fund_df['schemeName'] == fund]['schemeCode'].values[0]
                data = get_fund_data(code)

                if not data or 'data' not in data:
                    continue

                df = pd.DataFrame(data['data'])

                df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
                df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
                df = df.dropna().sort_values("date")

                if df.empty:
                    continue

                today = df['date'].max()

                if timeframe == "3 Months":
                    cutoff = today - timedelta(days=90)
                elif timeframe == "1 Year":
                    cutoff = today - timedelta(days=365)
                elif timeframe == "3 Years":
                    cutoff = today - timedelta(days=1095)
                else:
                    cutoff = today - timedelta(days=1825)

                df = df[df['date'] >= cutoff]

                df['returns'] = df['nav'].pct_change()

                avg_return = df['returns'].mean() * 252
                risk = df['returns'].std() * np.sqrt(252)

                if risk == 0:
                    continue

                sharpe = (avg_return - 0.06) / risk

                results.append({
                    "Fund": fund,
                    "Return": avg_return,
                    "Risk": risk,
                    "Sharpe": sharpe
                })

            except:
                continue

# -----------------------------
# DISPLAY
# -----------------------------
if results:

    df_res = pd.DataFrame(results).dropna()

    st.subheader("🏆 Best Fund Overview")

    best = df_res.sort_values(by="Sharpe", ascending=False).iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Best Fund", best['Fund'])
    c2.metric("📈 Return", f"{best['Return']:.2%}")
    c3.metric("⚖️ Sharpe", f"{best['Sharpe']:.2f}")

    st.divider()

    st.subheader("📊 Fund Comparison")

    df_res = df_res.sort_values(by="Sharpe", ascending=False)

    st.dataframe(df_res.style.format({
        "Return": "{:.2%}",
        "Risk": "{:.2%}",
        "Sharpe": "{:.2f}"
    }))

    # Scatter Plot
    st.subheader("📈 Risk vs Return")

    fig = px.scatter(
        df_res,
        x="Risk",
        y="Return",
        text="Fund",
        hover_name="Fund"
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        transition=dict(duration=500)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Portfolio
    st.subheader("💼 Portfolio Allocation")

    sharpe_vals = df_res['Sharpe'].clip(lower=0)
    weights = sharpe_vals / sharpe_vals.sum()

    df_res['Weight'] = weights

    fig2 = px.bar(df_res, x="Fund", y="Weight", text_auto=True)

    fig2.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig2, use_container_width=True)

    if st.button("🚀 Optimize Portfolio"):
        st.success("Portfolio optimized using Sharpe Ratio 🚀")

else:
    st.info("👈 Select funds to begin analysis")
