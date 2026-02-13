import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import time

st.set_page_config(page_title="TSX Signal Engine PRO", layout="wide")

st.title("🇨🇦 TSX LEVEL 2 Signal Engine")

st.caption("15-minute live momentum scanner | Auto-refresh 60s")

# ======================
# SETTINGS
# ======================

ACCOUNT_SIZE = 100000
RISK_PERCENT = 1

stocks = [
    "SHOP.TO","SU.TO","RY.TO","TD.TO","BNS.TO","ENB.TO",
    "CNQ.TO","CP.TO","CNR.TO","BAM.TO","TRP.TO","MFC.TO",
    "WCN.TO","ATD.TO","CM.TO","FTS.TO","POW.TO","IFC.TO",
    "NA.TO","CAR.TO","CSU.TO","L.TO","GIL.TO","MRU.TO",
    "NTR.TO","ABX.TO","TECK-B.TO","AEM.TO","BCE.TO","QSR.TO"
]

results = []

# ======================
# SCANNER LOOP
# ======================

for ticker in stocks:

    df = yf.download(ticker, period="7d", interval="15m")

    if df.empty:
        continue

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df["Close"]

    df["EMA20"] = ta.trend.ema_indicator(close, window=20)
    df["EMA50"] = ta.trend.ema_indicator(close, window=50)
    df["EMA200"] = ta.trend.ema_indicator(close, window=200)
    df["RSI"] = ta.momentum.rsi(close, window=14)
    df["ATR"] = ta.volatility.average_true_range(
        df["High"], df["Low"], df["Close"], window=14
    )

    last = df.iloc[-1]

    score = 0

    # Trend confirmation
    if last["EMA20"] > last["EMA50"] > last["EMA200"]:
        score += 2

    # Price above short EMA
    if last["Close"] > last["EMA20"]:
        score += 1

    # RSI momentum
    if 55 < last["RSI"] < 75:
        score += 1

    entry = float(last["Close"])
    atr = float(last["ATR"])

    stop_loss = entry - atr
    take_profit = entry + (2 * atr)

    # Risk sizing
    risk_amount = ACCOUNT_SIZE * (RISK_PERCENT / 100)
    shares = int(risk_amount / (entry - stop_loss)) if (entry - stop_loss) > 0 else 0

    confidence = round((score / 4) * 100, 0)

    results.append({
        "Stock": ticker,
        "Price": round(entry, 2),
        "Entry": round(entry, 2),
        "Stop": round(stop_loss, 2),
        "Target": round(take_profit, 2),
        "RSI": round(float(last["RSI"]), 2),
        "Confidence %": confidence,
        "Shares (1% Risk)": shares,
        "Score": score
    })

# ======================
# DISPLAY
# ======================

if len(results) == 0:
    st.error("No signals found right now.")
else:

    results_df = pd.DataFrame(results)
    best = results_df.sort_values(by="Score", ascending=False).iloc[0]

    st.subheader("🔥 BEST TRADE RIGHT NOW")

    col1, col2, col3 = st.columns(3)
    col1.metric("Stock", best["Stock"])
    col2.metric("Price", best["Price"])
    col3.metric("Confidence", f"{best['Confidence %']}%")

    st.write("### Trade Plan")
    st.write(f"Entry: {best['Entry']}")
    st.write(f"Stop: {best['Stop']}")
    st.write(f"Target: {best['Target']}")
    st.write(f"Shares (1% Risk): {best['Shares (1% Risk)']}")

    st.divider()
    st.write("### 📊 Ranked Signals")
    st.dataframe(results_df.sort_values(by="Score", ascending=False))

# Auto refresh
time.sleep(60)
st.rerun()
