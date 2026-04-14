import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
from datetime import timedelta

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="AlphaWealth AI", layout="wide")

# -----------------------------
# LOGIN SYSTEM
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 AlphaWealth AI Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "admin" and pwd == "admin":
            st.session_state.logged_in = True
        else:
            st.error("Invalid credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

# -----------------------------
# PREMIUM UI CSS
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #0f172a, #020617);
    color: #e2e8f0;
}
.glass {
    background: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 16px;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 15px;
}
.fade-in {
    animation: fadeIn 0.8s ease-in-out;
}
@keyframes fadeIn {
    from {opacity: 0; transform: translateY(20px);}
    to {opacity: 1; transform: translateY(0);}
}
@keyframes shimmer {
    0% {background-position: -200% 0;}
    100% {background-position: 200% 0;}
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown("## 💼 AlphaWealth AI Dashboard")
st.caption("Hedge Fund Level Portfolio Optimization")

# -----------------------------
# DATA
# -----------------------------
@st.cache_data(ttl=3600)
def get_funds():
    try:
        return pd.DataFrame(requests.get("https://api.mfapi.in/mf").json()).head(200)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_data(code):
    try:
        return requests.get(f"https://api.mfapi.in/mf/{code}").json()
    except:
        return None

fund_df = get_funds()

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("🔍 Controls")

search = st.sidebar.text_input("Search Fund")
investment = st.sidebar.number_input("Investment ₹", value=5000000)

filtered = fund_df.copy()
if search:
    filtered = filtered[filtered['schemeName'].str.contains(search, case=False)]

selected = st.multiselect("Select Funds", filtered['schemeName'])

# -----------------------------
# SKELETON LOADER
# -----------------------------
def skeleton():
    for _ in range(3):
        st.markdown("""
        <div style="height:80px;background:linear-gradient(90deg,#1e293b 25%,#334155 50%,#1e293b 75%);
        background-size:200% 100%;animation:shimmer 1.5s infinite;border-radius:10px;"></div>
        """, unsafe_allow_html=True)

# -----------------------------
# PROCESS
# -----------------------------
results = []

if selected:
    skeleton()

    for f in selected:
        try:
            code = fund_df[fund_df['schemeName']==f]['schemeCode'].values[0]
            data = get_data(code)
            df = pd.DataFrame(data['data'])

            df['nav'] = pd.to_numeric(df['nav'])
            df['date'] = pd.to_datetime(df['date'], dayfirst=True)

            df = df.sort_values("date").tail(365)
            df['returns'] = df['nav'].pct_change()

            ret = df['returns'].mean()*252
            risk = df['returns'].std()*np.sqrt(252)

            if risk == 0: continue

            sharpe = (ret - 0.06)/risk

            results.append({
                "Fund": f,
                "Return": ret,
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

    # Optimization
    weights = df_res['Sharpe'].clip(lower=0)
    weights /= weights.sum()

    df_res['Weight %'] = weights*100
    df_res['Investment ₹'] = weights*investment

    # Metrics
    best = df_res.sort_values("Sharpe", ascending=False).iloc[0]

    col1,col2,col3 = st.columns(3)
    col1.metric("🏆 Best Fund", best['Fund'])
    col2.metric("📈 Return", f"{best['Return']:.2%}")
    col3.metric("⚖️ Sharpe", f"{best['Sharpe']:.2f}")

    st.divider()

    # Chart
    st.markdown('<div class="glass fade-in">', unsafe_allow_html=True)

    fig = px.bar(df_res.head(5), x="Investment ₹", y="Fund", orientation='h')
    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Monte Carlo
    st.subheader("📉 Monte Carlo Simulation")

    sims = []
    for _ in range(500):
        w = np.random.random(len(df_res))
        w /= w.sum()
        sims.append(np.sum(w * df_res['Return']))

    sim_df = pd.DataFrame(sims, columns=["Returns"])
    st.plotly_chart(px.histogram(sim_df, x="Returns"))

# -----------------------------
# CALCULATOR
# -----------------------------
st.divider()
st.subheader("🧮 Financial Calculator")

c1,c2,c3 = st.columns(3)

with c1:
    p = st.number_input("Investment ₹", value=500000)

with c2:
    r = st.number_input("Return %", value=12.0)

with c3:
    y = st.number_input("Years", value=5)

fv = p*(1+r/100)**y
st.success(f"Final Value: ₹{fv:,.0f}")

sip = st.number_input("Monthly SIP ₹", value=10000)
months = y*12
mr = r/12/100

sip_val = sip*(((1+mr)**months -1)/mr)*(1+mr)
st.info(f"SIP Value: ₹{sip_val:,.0f}")
