# 📊 Mutual Fund Analytics & Portfolio Optimization Dashboard

## 🚀 Project Overview

This project is a **fintech-style mutual fund analytics dashboard** built using **Python, Streamlit, and Plotly**.

It enables users to:
- Analyze mutual fund performance using real-time NAV data
- Compare multiple funds across different timeframes
- Evaluate investments using risk-adjusted metrics
- Generate portfolio allocation suggestions

---

## ✨ Key Features

### 🔍 Dynamic Fund Selection
- Select multiple mutual funds from a live dataset
- No manual scheme code entry required

### 📅 Timeframe Analysis
- 3 Months  
- 1 Year  
- 3 Years  
- 5 Years  

### 📊 Advanced Metrics
- 📈 Annualized Return  
- 📉 Risk (Volatility)  
- ⚖️ Sharpe Ratio  

### 🏆 Best Fund Recommendation
- Automatically identifies the best-performing fund
- Based on highest Sharpe Ratio

### 💼 Portfolio Allocation
- Suggests optimal weights for selected funds
- Based on risk-adjusted performance

### 📈 Interactive Visualizations
- Plotly-powered charts:
  - Risk vs Return scatter plot
  - Portfolio allocation bar chart

---

## 🧠 Methodology

The system performs the following steps:

1. Fetches real-time NAV data from API  
2. Cleans and preprocesses data  
3. Calculates daily returns  
4. Computes:
   - Annualized Return
   - Standard Deviation (Risk)
   - Sharpe Ratio  
5. Compares selected funds  
6. Recommends best fund  
7. Allocates portfolio weights proportionally  

---

## 🛠️ Tech Stack

- **Python**
- **Streamlit** – UI & deployment  
- **Pandas** – data processing  
- **NumPy** – numerical computation  
- **Requests** – API calls  
- **Plotly** – interactive visualization  

---

## 🌐 Data Source

- Mutual Fund API: https://mfapi.in/

---

## ▶️ How to Run Locally

1. Clone the repository:
```bash
git clone https://github.com/your-username/mutual-fund-tool.git
cd mutual-fund-tool
