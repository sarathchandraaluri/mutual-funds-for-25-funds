import streamlit as st
import pandas as pd
import requests
import numpy as np
import plotly.express as px
from datetime import timedelta

st.set_page_config(page_title="Mutual Fund Elite Tool", layout="wide")

st.title("📊 Mutual Fund Analytics & Portfolio Optimization Tool")

# -----------------------------
# FALLBACK DATA WITH CATEGORY
# -----------------------------
fallback_data = [
    {"schemeName": "Axis Bluechip Fund", "schemeCode": "120503", "category": "Large Cap"},
    {"schemeName": "HDFC Top 100 Fund", "schemeCode": "118989", "category": "Large Cap"},
    {"schemeName": "ICICI Prudential Bluechip Fund", "schemeCode": "119551", "category": "Large Cap"},
    {"schemeName": "SBI Bluechip Fund", "schemeCode": "118834", "category": "Large Cap"},
    {"schemeName": "Kotak Bluechip Fund", "schemeCode": "120828", "category": "Large Cap"},

    {"schemeName": "Parag Parikh Flexi Cap Fund", "schemeCode": "122639", "category": "Flexi Cap"},
    {"schemeName": "Axis Flexi Cap Fund", "schemeCode": "120716", "category": "Flexi Cap"},
    {"schemeName": "HDFC Flexi Cap Fund", "schemeCode": "118550", "category": "Flexi Cap"},
    {"schemeName": "ICICI Prudential Flexi Cap Fund", "schemeCode": "119551", "category": "Flexi Cap"},
    {"schemeName": "Kotak Flexi Cap Fund", "schemeCode": "120828", "category": "Flexi Cap"},

    {"schemeName": "SBI Small Cap Fund", "schemeCode": "125354", "category": "Small Cap"},
    {"schemeName": "Nippon India Small Cap Fund", "schemeCode": "125354", "category": "Small Cap"},
    {"schemeName": "Axis Small Cap Fund", "schemeCode": "125497", "category": "Small Cap"},
    {"schemeName": "HDFC Small Cap Fund", "schemeCode": "118550", "category": "Small Cap"},
    {"schemeName": "Kotak Small Cap Fund", "schemeCode": "122639", "category": "Small Cap"},

    {"schemeName": "UTI Nifty Index Fund", "schemeCode": "120716", "category": "Index"},
    {"schemeName": "Nippon India Large Cap Fund", "schemeCode": "118551", "category": "Large Cap"},
    {"schemeName": "Mirae Asset Large Cap Fund", "schemeCode": "118989", "category": "Large Cap"},
    {"schemeName": "Franklin India Bluechip Fund", "schemeCode": "118834", "category": "Large Cap"},
    {"schemeName": "Aditya Birla Frontline Equity Fund", "schemeCode": "119064", "category": "Large Cap"},

    {"schemeName": "ICICI Prudential Balanced Advantage Fund", "schemeCode": "120586", "category": "Hybrid"},
    {"schemeName": "HDFC Balanced Advantage Fund", "schemeCode": "119064", "category": "Hybrid"},
    {"schemeName": "SBI Equity Hybrid Fund", "schemeCode": "118834", "category": "Hybrid"},
    {"schemeName": "Kotak Equity Hybrid Fund", "schemeCode": "120828", "category": "Hybrid"},
    {"schemeName": "Aditya Birla Hybrid Equity Fund", "schemeCode": "119551", "category": "Hybrid"},
]

# -----------------------------
# FETCH FUND LIST
# -----------------------------
@st.cache_data
def get_fund_list():
    try:
        res = requests.get("https://api.mfapi.in/mf", timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json()).head(150)
            return df
    except:
        pass
    return pd.DataFrame(fallback_data)

fund_df = get_fund_list()

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("🔍 Filter Options")

category = st.sidebar.selectbox(
    "Category",
    ["All", "Large Cap", "Flexi Cap", "Small Cap", "Hybrid", "Index"]
)

search = st.sidebar.text_input("Search Fund")

filtered_df = fund_df.copy()

if category != "All" and 'category' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['category'] == category]

if search:
    filtered_df = filtered_df[
        filtered_df['schemeName'].str.contains(search, case=False, na=False)
    ]

# -----------------------------
# INPUTS
# -----------------------------
selected_funds = st.multiselect(
    "Select Mutual Funds",
    filtered_df['schemeName']
)

timeframe = st.selectbox(
    "Timeframe",
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
# DISPLAY
# -----------------------------
if results:

    df_res = pd.DataFrame(results)

    df_res = df_res.replace([np.inf, -np.inf], np.nan).dropna()

    if df_res.empty:
        st.warning("No valid data")
        st.stop()

    # SORT
    sort_by = st.selectbox("Sort By", ["Sharpe", "Return", "Risk"])
    df_res = df_res.sort_values(by=sort_by, ascending=False)

    # KPI
    best = df_res.iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Best Fund", best['Fund'])
    c2.metric("📈 Return", f"{best['Return']:.2%}")
    c3.metric("⚖️ Sharpe", f"{best['Sharpe']:.2f}")

    # TABLE
    st.subheader("📊 Comparison")
    st.dataframe(df_res.style.format({
        "Return": "{:.2%}",
        "Risk": "{:.2%}",
        "Sharpe": "{:.2f}"
    }))

    # SCATTER
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
    weights = sharpe_vals / sharpe_vals.sum()

    df_res['Weight'] = weights

    fig2 = px.bar(df_res, x="Fund", y="Weight", text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Select funds to analyze")
