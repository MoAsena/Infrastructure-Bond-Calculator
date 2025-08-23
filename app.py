import streamlit as st
import pandas as pd
import numpy as np
from openpyxl import load_workbook
from datetime import datetime
from dateutil.relativedelta import relativedelta

EXCEL_PATH = "Infrastruture Bonds.xlsx"

@st.cache_data
def load_wb():
    try:
        wb = load_workbook(EXCEL_PATH, data_only=False, read_only=False)
        return wb
    except Exception as e:
        return None

def calculate_consideration(face_value, clean_price, coupon_rate, trade_date, settlement_date, freq, commission_rate, other_fees):
    # Days between last coupon and settlement
    days_in_year = 365
    last_coupon_date = settlement_date - relativedelta(months=12//freq)
    accrued_days = (settlement_date - last_coupon_date).days
    accrued_interest = face_value * coupon_rate/freq * (accrued_days/(days_in_year/freq))

    clean_amount = face_value * (clean_price/100)
    dirty_amount = clean_amount + accrued_interest

    commission = commission_rate * clean_amount
    vat = 0.16 * commission
    nse_fee = 0.00012 * clean_amount
    cdsc_fee = 0.00012 * clean_amount
    cma_fee = 0.00015 * clean_amount

    total = dirty_amount + commission + vat + nse_fee + cdsc_fee + cma_fee + other_fees
    return {
        "Clean Amount": clean_amount,
        "Accrued Interest": accrued_interest,
        "Dirty Amount": dirty_amount,
        "Commission": commission,
        "VAT (16%)": vat,
        "NSE Fee": nse_fee,
        "CDSC Fee": cdsc_fee,
        "CMA Fee": cma_fee,
        "Other Fees": other_fees,
        "Total Consideration": total
    }

st.title("📊 Bond Consideration Calculator")

face_value = st.number_input("Face Value (KES)", min_value=1000, step=1000, value=1000000)
clean_price = st.number_input("Clean Price (%)", min_value=50.0, step=0.01, value=95.00)
coupon_rate = st.number_input("Coupon Rate (%)", min_value=0.1, step=0.01, value=12.50) / 100
freq = st.selectbox("Coupon Frequency", [1, 2, 4], index=1)
trade_date = st.date_input("Trade Date", datetime.today())
settlement_date = st.date_input("Settlement Date", datetime.today() + pd.Timedelta(days=3))

commission_rate = st.number_input("Commission Rate (%)", min_value=0.0, value=0.35) / 100
other_fees = st.number_input("Other Flat Fees (KES)", min_value=0.0, value=0.0)

if st.button("Calculate Consideration"):
    results = calculate_consideration(face_value, clean_price, coupon_rate, trade_date, settlement_date, freq, commission_rate, other_fees)
    st.subheader("📑 Fee Breakdown")
    st.write(pd.DataFrame(results.items(), columns=["Item", "KES"]).set_index("Item"))

    st.success(f"💰 Total Consideration: KES {results['Total Consideration']:,.2f}")

st.sidebar.header("📂 Backend: Excel File Viewer")
wb = load_wb()
if wb:
    sheetnames = wb.sheetnames
    sheet = st.sidebar.selectbox("Select Sheet", sheetnames)
    if st.sidebar.button("Show Data"):
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet)
        st.dataframe(df)
else:
    st.sidebar.warning("Upload `Infrastruture Bonds.xlsx` to view data.")
