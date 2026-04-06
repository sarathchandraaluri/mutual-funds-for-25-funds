import streamlit as st
import pandas as pd
import requests
import numpy as np
import plotly.express as px
from datetime import timedelta

st.set_page_config(page_title="Mutual Fund Elite Tool", layout="wide")

st.title("📊 Mutual Fund Analytics & Portfolio Optimization Tool")

# -----------------------------
# FALLBACK (SAFE FUNDS)
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
    {"schemeName": "SBI Small Cap Fund", "schemeCode": "125354"},
    {"schemeName": "UTI Nifty Index Fund", "schemeCode": "120716"},
]

# -----------------------------
# FETCH FUND LIST
# -----------------------------
@st.cache_data
def get_fund_list():
    try:
        res = requests.get("https://api.mfapi.in/mf", timeout=10)
        if res.status_code == 200:
            return pd.DataFrame(res.json()).head(100)
    except:
        pass
    return pd.DataFrame(fallback_data)

fund_df = get_fund_list()

# -----------------------------
# INPUTS
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    selected_funds = st.multiselect("🔍 Select Funds", fund_df['schemeName'])

with col2:
    timeframe = st.selectbox(
        "📅 Timeframe",
        ["3 Months", "1 Year", "2 Years", "3 Years", "5 Years"]
    )

results = []

# -----------------------------
# PROCESS DATA
# -----------------------------
for fund in selected_funds:
    try:
        code = fund_df[fund_df['schemeName'] == fund]['schemeCode'].values[0]
        url = f"https://api.mfapi.in/mf/{code}"

        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            continue

        data = res.json()
        if 'data' not in data:
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
        elif timeframe == "2 Years":
            cutoff = today - timedelta(days=730)
        elif timeframe == "3 Years":
            cutoff = today - timedelta(days=1095)
        else:
            cutoff = today - timedelta(days=1825)

        df = df[df['date'] >= cutoff]

        if df.empty:
            continue

        df['returns'] = df['nav'].pct_change()

        avg_return = df['returns'].mean() * 252
        risk = df['returns'].std() * np.sqrt(252)

        if risk == 0 or np.isnan(risk):
            continue

        sharpe = (avg_return - 0.06) / risk

        if np.isnan(avg_return) or np.isnan(sharpe):
            continue

        results.append({
            "Fund": fund,
            "Return": avg_return,
            "Risk": risk,
            "Sharpe": sharpe
        })

    except:
        continue

# -----------------------------
# DISPLAY RESULTS
# -----------------------------
if results:

    df_res = pd.DataFrame(results)

    # CLEAN DATA
    df_res = df_res.replace([np.inf, -np.inf], np.nan).dropna()

    if df_res.empty:
        st.warning("No valid data available")
        st.stop()

    # KPI
    best = df_res.loc[df_res['Sharpe'].idxmax()]

    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Best Fund", best['Fund'])
    c2.metric("📈 Return", f"{best['Return']:.2%}")
    c3.metric("⚖️ Sharpe", f"{best['Sharpe']:.2f}")

    # TABLE
    st.subheader("📊 Fund Comparison")
    st.dataframe(df_res.style.format({
        "Return": "{:.2%}",
        "Risk": "{:.2%}",
        "Sharpe": "{:.2f}"
    }))

    # SAFE SCATTER (NO SIZE PARAM)
    st.subheader("📈 Risk vs Return")

    fig = px.scatter(
        df_res,
        x="Risk",
        y="Return",
        text="Fund",
        hover_name="Fund"
    )

    fig.update_traces(textposition='top center')

    st.plotly_chart(fig, use_container_width=True)

    # PORTFOLIO
    st.subheader("💼 Portfolio Allocation")

    sharpe_vals = df_res['Sharpe'].clip(lower=0)

    weights = sharpe_vals / sharpe_vals.sum() if sharpe_vals.sum() != 0 else [1/len(sharpe_vals)]*len(sharpe_vals)

    df_res['Weight'] = weights

    fig2 = px.bar(df_res, x="Fund", y="Weight", text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Select funds to begin analysis")
