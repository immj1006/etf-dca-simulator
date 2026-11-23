"""ETF DCA simulator: invest a fixed amount every month and see how it grows."""

import datetime

import pandas as pd
import streamlit as st
import yfinance as yf

st.title("ETF DCA Simulator")
st.write("Invest the same amount on the first trading day of every month.")


# ---------------------------------------------------------------------------
# Step 1: inputs from the user
# ---------------------------------------------------------------------------
ticker = st.text_input("Ticker", value="VOO").strip().upper()
monthly_amount = st.number_input("Monthly amount ($)", min_value=1, value=500, step=50)
start_date = st.date_input(
    "Start date",
    value=datetime.date(2020, 1, 1),
    max_value=datetime.date.today(),
)


# ---------------------------------------------------------------------------
# Step 2: download daily closing prices
# ---------------------------------------------------------------------------
# @st.cache_data remembers the result, so moving a widget doesn't
# re-download the same prices from Yahoo every time.
@st.cache_data
def get_prices(ticker, start_date):
    history = yf.Ticker(ticker).history(start=start_date, auto_adjust=True)
    return history["Close"]


prices = get_prices(ticker, start_date)

if prices.empty:
    st.error(f"No price data found for '{ticker}'. Check the ticker symbol.")
    st.stop()


# ---------------------------------------------------------------------------
# Step 3: simulate buying once a month
# ---------------------------------------------------------------------------
# Group the daily prices by (year, month) and keep the first day of each group.
# Those are our "buy days".
buy_prices = prices.groupby([prices.index.year, prices.index.month]).head(1)

# Build one table with a row per trading day.
df = pd.DataFrame({"Price": prices})

# On buy days: how much cash went in, and how many shares it bought.
# On other days these are 0.
df["Cash added"] = 0.0
df.loc[buy_prices.index, "Cash added"] = monthly_amount
df["Shares bought"] = df["Cash added"] / df["Price"]

# Running totals: cumsum() adds up everything up to and including each row.
df["Total invested"] = df["Cash added"].cumsum()
df["Shares owned"] = df["Shares bought"].cumsum()
df["Portfolio value"] = df["Shares owned"] * df["Price"]


# ---------------------------------------------------------------------------
# Step 4: show the results
# ---------------------------------------------------------------------------
total_invested = df["Total invested"].iloc[-1]   # iloc[-1] = last row
current_value = df["Portfolio value"].iloc[-1]
gain = current_value - total_invested
gain_pct = gain / total_invested * 100

col1, col2, col3 = st.columns(3)
col1.metric("Total invested", f"${total_invested:,.0f}")
col2.metric("Current value", f"${current_value:,.0f}")
col3.metric("Gain / loss", f"${gain:,.0f}", f"{gain_pct:.1f}%")

st.subheader(f"{ticker}: total invested vs portfolio value")
st.line_chart(
    df[["Portfolio value", "Total invested"]],
    color=["#2a78d6", "#eb6834"],  # blue = value, orange = invested
    x_label="Date",
    y_label="US dollars",
)

st.caption(
    f"{len(buy_prices)} monthly purchases. Prices are adjusted for splits and "
    "dividends, so this assumes dividends were reinvested."
)

with st.expander("See the monthly purchases"):
    purchases = df.loc[buy_prices.index, ["Price", "Shares bought", "Shares owned"]]
    st.dataframe(purchases)
