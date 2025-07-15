
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Stock Fair Value App", layout="wide")

# Title
st.title("📈 Stock Fair Value Estimator (EV/EBITDA Method)")

# Valuation logic
def ev_valuation(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5y")

        if hist.empty:
            return None

        current_price = hist["Close"][-1]
        ebitda = info.get("ebitda", None)
        ev = info.get("enterpriseValue", None)

        if ebitda and ev and ebitda != 0:
            ev_ebitda = ev / ebitda
            fair_value = ebitda * ev_ebitda
            undervalued_pct = ((fair_value - current_price) / current_price) * 100

            return {
                "Ticker": ticker,
                "Current Price": round(current_price, 2),
                "EBITDA": round(ebitda, 2),
                "Enterprise Value": round(ev, 2),
                "EV/EBITDA": round(ev_ebitda, 2),
                "Fair Value": round(fair_value, 2),
                "Undervalued (%)": round(undervalued_pct, 2)
            }
    except Exception as e:
        print(f"Error for {ticker}: {e}")
    return None

# Search bar for on-demand stock analysis
st.markdown("## 🔍 On-Demand Stock Valuation (EV Method)")
search_ticker = st.text_input("Enter a stock ticker (e.g., AAPL, INFY.NS)")

if search_ticker:
    st.info(f"Fetching valuation for {search_ticker.upper()}...")
    result = ev_valuation(search_ticker.upper())
    if result:
        st.success("Valuation complete!")
        st.dataframe(pd.DataFrame([result]), use_container_width=True)
    else:
        st.error("Unable to fetch data or calculate fair value for this ticker.")
