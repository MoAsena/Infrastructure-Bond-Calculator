import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from openpyxl import load_workbook

EXCEL_FILE = "Infrastruture Bonds.xlsx"

# --- Cached workbook loader ---
@st.cache_data
def load_workbook_data():
    xls = pd.ExcelFile(EXCEL_FILE)
    return xls, xls.sheet_names

# --- Compute consideration ---
def compute_consideration(df, face_value, trade_date):
    df['Date'] = pd.to_datetime(df['Date'])
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.dropna()
    df = df[df['Date'] >= trade_date]

    clean_price = 100
    coupon_rate = df['Amount'].iloc[0] / face_value
    days_in_year = 365
    last_coupon_date = df['Date'].min() - pd.Timedelta(days=182)
    accrued_days = (trade_date - last_coupon_date).days
    accrued_interest = face_value * coupon_rate * accrued_days / days_in_year

    dirty_price = clean_price + (accrued_interest / face_value) * 100
    gross = face_value * dirty_price / 100

    # Fees
    commission = gross * 0.002
    excise = commission * 0.15
    cds = 100
    total_charges = commission + excise + cds

    consideration = gross + total_charges

    return {
        "Dirty Price": dirty_price,
        "Gross": gross,
        "Commission": commission,
        "Excise": excise,
        "CDS": cds,
        "Total Charges": total_charges,
        "Consideration": consideration,
        "Cashflows": df
    }

# --- Streamlit UI ---
st.title("Infrastructure Bond Consideration Calculator")

xls, sheet_names = load_workbook_data()

bond = st.sidebar.selectbox("Select Bond", sheet_names)

face_value = st.number_input("Face Value (KES)", value=1_000_000, step=100000)
trade_date = st.date_input("Trade / Value Date", datetime.today())

df = pd.read_excel(EXCEL_FILE, sheet_name=bond)
results = compute_consideration(df, face_value, pd.to_datetime(trade_date))

st.subheader("Client View")
st.write(f"**Face Value:** {face_value:,.0f}")
st.write(f"**Consideration:** {results['Consideration']:,.2f}")
st.write(f"**Trade/Value Date:** {trade_date}")
st.write(f"**Dirty Price:** {results['Dirty Price']:.4f}")

st.subheader("Cashflows")
st.dataframe(results['Cashflows'])

st.subheader("Charges")
st.write(f"Commission: {results['Commission']:,.2f}")
st.write(f"Excise Duty: {results['Excise']:,.2f}")
st.write(f"CDS Fees: {results['CDS']:,.2f}")
st.write(f"**Total Charges: {results['Total Charges']:,.2f}**")
