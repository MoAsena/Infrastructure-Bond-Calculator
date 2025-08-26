import streamlit as st
import pandas as pd

# Fee calculation
def calculate_fees(consideration):
    brokerage_commission = max(1000, 0.00035 * consideration)
    other_levies = 0.00035 * consideration
    vat = 0.16 * brokerage_commission
    total_charges = brokerage_commission + other_levies + vat
    return brokerage_commission, other_levies, vat, total_charges

# Cashflow calculation based on face value and coupon schedule
def calculate_cashflows(df, face_value):
    df["Cashflow"] = (df["CouponRate"] / 100 * face_value / df["Frequency"]) + (df["Principal"] * face_value)
    return df[["Trade Date", "Cashflow"]]

def main():
    st.title("Infrastructure Bond Calculator")
    st.sidebar.header("Select Parameters")

    xls = pd.ExcelFile("Infrastruture Bonds.xlsx")
    sheet_names = xls.sheet_names

    bond_choice = st.sidebar.selectbox("Select Bond", sheet_names)
    df = pd.read_excel(xls, sheet_name=bond_choice)

    face_value = st.number_input("Face Value", min_value=1000000, step=1000000, value=1000000)
    trade_date = st.date_input("Trade Date")

    # Consideration from Excel
    consideration = df["Consideration"].iloc[0]

    # Fee calculation
    brokerage_commission, other_levies, vat, total_charges = calculate_fees(consideration)
    amount_payable = consideration + total_charges

    # Show results
    st.subheader("Bond Summary")
    st.write(f"**Face Value:** {face_value:,}")
    st.write(f"**Consideration:** {consideration:,.2f}")
    st.write(f"**Trade Date:** {trade_date}")
    st.write(f"**Dirty Price:** {df['Dirty Price'].iloc[0]:.2f}")

    st.subheader("Charges")
    st.write(f"Brokerage Commission: {brokerage_commission:,.2f}")
    st.write(f"Other Levies: {other_levies:,.2f}")
    st.write(f"VAT: {vat:,.2f}")
    st.write(f"**Total Charges:** {total_charges:,.2f}")
    st.write(f"**Amount Payable/Receivable:** {amount_payable:,.2f}")

    # Cashflows
    st.subheader("Cashflows")
    cashflows = calculate_cashflows(df, face_value)
    st.dataframe(cashflows)

if __name__ == "__main__":
    main()
