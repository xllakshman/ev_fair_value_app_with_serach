import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Stock Fair Value Analyzer", layout="wide")
st.title("📈 Stock Fair Value Estimator (EV/EBITDA Method)")


GITHUB_CSV_URL = "https://raw.githubusercontent.com/xllakshman/ev_fair_value_app_with_serach/main/stock_list.csv"

def get_fair_value(ticker, growth_rate=0.10):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        ev = info.get("enterpriseValue")
        ebitda = info.get("ebitda")
        shares = info.get("sharesOutstanding")
        current_price = info.get("currentPrice")
        if not (ev and ebitda and shares):
            return None, None
        ev_ebitda_ratio = ev / ebitda
        projected_ebitda = ebitda * (1 + growth_rate)
        projected_ev = projected_ebitda * ev_ebitda_ratio
        fair_price = projected_ev / shares
        return fair_price, current_price
    except:
        return None, None

def ev_valuation(ticker):
    try:
        ticker = ticker.upper()
        fair_price, current_price = get_fair_value(ticker)
        if fair_price is None or current_price is None:
            return None
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="3y")
        company_name = info.get("shortName", "N/A")
        market_cap = info.get("marketCap", 0)
        industry = info.get("industry", "N/A")
        cap_type = (
            "Mega" if market_cap >= 200_000_000_000 else
            "Large" if market_cap >= 10_000_000_000 else
            "Mid" if market_cap >= 2_000_000_000 else "Small"
        )
        market = "India" if ticker.endswith(".NS") else "USA"
        underval_pct = ((fair_price - current_price) / current_price) * 100
        if fair_price < 0 or underval_pct < 5:
            band = "Over Valued"
        elif underval_pct > 30:
            band = "Deep Discount"
        elif underval_pct > 20:
            band = "High Value"
        elif underval_pct > 18:
            band = "Undervalued"
        else:
            band = "Fair/Premium"
        high_3y = hist["High"].max() if not hist.empty else None
        low_3y = hist["Low"].min() if not hist.empty else None
        entry_price = round(low_3y * 1.05, 2) if low_3y else "N/A"
        exit_price = round(high_3y * 0.95, 2) if high_3y else "N/A"
        return {
            "Symbol": ticker,
            "Name": company_name,
            "Fair Value (EV)": round(fair_price, 2),
            "Current Price": round(current_price, 2),
            "Undervalued (%)": round(underval_pct, 2),
            "Valuation Band": band,
            "Market": market,
            "Cap Size": cap_type,
            "Industry": industry,
            "3Y High": round(high_3y, 2) if high_3y else "N/A",
            "3Y Low": round(low_3y, 2) if low_3y else "N/A",
            "Entry Price": entry_price,
            "Exit Price": exit_price,
            "Signal": "Buy" if fair_price > current_price else "Hold/Sell"
        }
    except:
        return None

st.markdown("## 🔍 On-Demand Stock Valuation (EV Method)")
search_ticker = st.text_input("Enter a stock ticker in Capitals(e.g., AAPL, INFY.NS)")
if search_ticker:
    st.info(f"Fetching valuation for {search_ticker}...")
    result = ev_valuation(search_ticker)
    if result:
        st.success("Valuation complete!")
        st.dataframe(pd.DataFrame([result]), use_container_width=True)
    else:
        st.error("Unable to fetch data or calculate fair value for this ticker.")


def process_symbols(df):
    results = []
    for ticker in df["Symbol"]:
        row = ev_valuation(ticker)
        if row:
            results.append(row)
    return pd.DataFrame(results)

if "output_df" not in st.session_state:
    st.session_state["output_df"] = None
if "csv_data" not in st.session_state:
    st.session_state["csv_data"] = None

uploaded_file = st.file_uploader("Upload CSV with tickers of your choice (ensure 'Symbol' as header)", type="csv")
col1, col2 = st.columns([1, 1])
with col1:
    run_uploaded = st.button("Run Uploaded File")
with col2:
    run_default = st.button("Show All Stocks")

if run_uploaded and uploaded_file:
    df = pd.read_csv(uploaded_file)
    if "Symbol" not in df.columns:
        st.error("CSV must contain a column named 'Symbol'")
    else:
        st.success(f"Processing Default {len(df)} uploaded tickers, Please wait, otherwise, upload a fresh ticker of your choice via csv...")
        output_df = process_symbols(df)
        if not output_df.empty:
            st.session_state["output_df"] = output_df
            st.session_state["csv_data"] = output_df.to_csv(index=False).encode("utf-8")
elif run_default or (uploaded_file is None and st.session_state["output_df"] is None):
    try:
        df = pd.read_csv(GITHUB_CSV_URL)
        st.success(f"Processing Default {len(df)} uploaded tickers, Please wait for 180 Sec, otherwise, upload a fresh ticker(s) of your choice via csv...")
        output_df = process_symbols(df)
        if not output_df.empty:
            st.session_state["output_df"] = output_df
            st.session_state["csv_data"] = output_df.to_csv(index=False).encode("utf-8")
    except:
        st.error("Failed to load from GitHub.")



# Display result in tabs with filter
if st.session_state["output_df"] is not None:
    tab1, tab2 = st.tabs(["📊 Filtered View", "📋 Full Raw Data"])
    with tab1:
        df = st.session_state["output_df"]
        with st.sidebar:
            st.markdown("### 🔍 Filter Options")
            selected_band = st.multiselect("Valuation Band", df["Valuation Band"].unique(), default=df["Valuation Band"].unique())
            selected_market = st.multiselect("Market", df["Market"].unique(), default=df["Market"].unique())
            selected_cap = st.multiselect("Cap Size", df["Cap Size"].unique(), default=df["Cap Size"].unique())
        filtered_df = df[
            df["Valuation Band"].isin(selected_band) &
            df["Market"].isin(selected_market) &
            df["Cap Size"].isin(selected_cap)
        ]
        st.dataframe(filtered_df.sort_values(by="Undervalued (%)", ascending=False), use_container_width=True)
        st.download_button("📥 Download Filtered Report as CSV",
                           data=filtered_df.to_csv(index=False).encode("utf-8"),
                           file_name="filtered_fair_value_report.csv",
                           mime="text/csv")
    with tab2:
        st.dataframe(st.session_state["output_df"].sort_values(by="Undervalued (%)", ascending=False), use_container_width=True)
        st.download_button("📥 Download Full Report as CSV",
                           data=st.session_state["csv_data"],
                           file_name="fair_value_report.csv",
                           mime="text/csv")

    with st.expander("📘 Column Glossary & Category Descriptions"):
        st.markdown("""
**Glossary:**

- **Symbol**: Stock ticker symbol (e.g., AAPL, INFY.NS)  
- **Name**: Full company name  
- **Fair Value (EV)**: Estimated intrinsic price based on EV/EBITDA model  
- **Current Price**: Latest market price from Yahoo Finance  
- **Undervalued (%)**: How much lower the current price is compared to fair value  
- **Valuation Band**: Classification based on discount level  
  - `Over Valued`: Fair value < 0 or undervalued < 5%  
  - `Fair/Premium`: Fair value near current price (5–18%)  
  - `Undervalued`: 18–20% undervalued  
  - `High Value`: 20–30% undervalued  
  - `Deep Discount`: >30% undervalued  
- **Market**: `India` or `USA`  
- **Cap Size**: Company size by market cap (`Mega`, `Large`, `Mid`, `Small`)  
- **Industry**: Sector of the company  
- **3Y High/Low**: Highest/lowest stock price in past 3 years  
- **Entry Price**: Suggested buy point (within 5% of 3Y low)  
- **Exit Price**: Suggested sell point (within 5% of 3Y high)  
- **Signal**: `Buy` if undervalued, otherwise `Hold/Sell`  
""")
