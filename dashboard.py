import streamlit as st
import pandas as pd
import requests
import numpy as np
import plotly.express as px
from datetime import timedelta

st.set_page_config(page_title="Mutual Fund Elite Tool", layout="wide")

# -----------------------------
# CUSTOM STYLING
# -----------------------------
st.markdown("""
<style>
.big-title {
    font-size: 32px;
    font-weight: bold;
}
.metric-card {
    background-color: #111;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">📊 Mutual Fund Analytics Dashboard</div>', unsafe_allow_html=True)

# -----------------------------
# FALLBACK FUNDS
# -----------------------------
fallback_data = [
    {"schemeName": "Axis Bluechip Fund", "schemeCode": "120503"},
    {"schemeName": "HDFC Top 100 Fund", "schemeCode": "118989"},
    {"schemeName": "ICICI Prudential Bluechip Fund", "schemeCode": "119551"},
    {"schemeName": "SBI Bluechip Fund", "schemeCode": "118834"},
    {"schemeName": "Kotak Bluechip Fund", "schemeCode": "120828"},
    {"schemeName": "Parag Parikh Flexi Cap Fund", "schemeCode": "122639"},
    {"schemeName": "Axis Flexi Cap Fund", "schemeCode": "120716"},
    {"schemeName": "HDFC Flexi Cap Fund", "schemeCode": "118550"},
    {"schemeName": "Kotak Flexi Cap Fund", "schemeCode": "118834"},
    {"schemeName": "ICICI Prudential Flexi Cap Fund", "schemeCode": "119551"},
]

@st.cache_data
def get_fund_list():
    try:
        res = requests.get("https://api.mfapi.in/mf", timeout=10)
        df = pd.DataFrame(res.json())
        return df.head(150)
    except:
        return pd.DataFrame(fallback_data)

fund_df = get_fund_list()

# -----------------------------
# INPUTS
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    selected_funds = st.multiselect("Select Funds", fund_df['schemeName'])

with col2:
    timeframe = st.selectbox("Timeframe", ["3 Months", "1 Year", "3 Years", "5 Years"])

results = []

# -----------------------------
# PROCESS DATA
# -----------------------------
for fund in selected_funds:

    code = fund_df[fund_df['schemeName'] == fund]['schemeCode'].values[0]
    url = f"https://api.mfapi.in/mf/{code}"

    try:
        data = requests.get(url, timeout=10).json()
        df = pd.DataFrame(data['data'])

        df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
        df['date'] = pd.to_datetime(df['date'], dayfirst=True)

        df = df.dropna().sort_values("date")

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
        sharpe = (avg_return - 0.06) / risk if risk != 0 else 0

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

    df_res = pd.DataFrame(results)

    # KPI CARDS
    best = df_res.loc[df_res['Sharpe'].idxmax()]

    c1, c2, c3 = st.columns(3)

    c1.metric("🏆 Best Fund", best['Fund'])
    c2.metric("📈 Return", f"{best['Return']:.2%}")
    c3.metric("⚖️ Sharpe", f"{best['Sharpe']:.2f}")

    # TABLE
    st.subheader("📊 Comparison Table")
    st.dataframe(df_res.style.format({
        "Return": "{:.2%}",
        "Risk": "{:.2%}",
        "Sharpe": "{:.2f}"
    }))

    # PLOTLY CHART
    st.subheader("📈 Risk vs Return")

    fig = px.scatter(
        df_res,
        x="Risk",
        y="Return",
        text="Fund",
        size="Sharpe",
        hover_name="Fund"
    )

    st.plotly_chart(fig, use_container_width=True)

    # BAR CHART
    st.subheader("📊 Portfolio Allocation")

    sharpe_vals = df_res['Sharpe'].clip(lower=0)

    weights = sharpe_vals / sharpe_vals.sum() if sharpe_vals.sum() != 0 else [1/len(sharpe_vals)]*len(sharpe_vals)

    df_res['Weight'] = weights

    fig2 = px.bar(df_res, x="Fund", y="Weight", text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Select funds to begin analysis")
