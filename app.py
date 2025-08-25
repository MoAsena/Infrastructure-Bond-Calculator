import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

EXCEL_PATH = "Infrastruture Bonds.xlsx"

@st.cache_data
def load_workbook_data():
    xls = pd.ExcelFile(EXCEL_PATH)
    data = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}
    return data, xls.sheet_names

def calculate_consideration(df, face_value, trade_date):
    df['Date'] = pd.to_datetime(df['Date'])
    cashflows = df[df['Date'] >= trade_date].copy()

    dirty_price = df['Price'].iloc[0]
    accrued_interest = df['Accrued'].iloc[0]
    charges = face_value * 0.02  
    consideration = face_value * dirty_price + accrued_interest + charges

    return {
        "face_value": face_value,
        "dirty_price": dirty_price,
        "accrued_interest": accrued_interest,
        "charges": charges,
        "consideration": consideration,
        "cashflows": cashflows[['Date', 'Cashflow']]
    }

def main():
    st.sidebar.title("Bond Calculator")
    data, sheet_names = load_workbook_data()
    bond_choice = st.sidebar.selectbox("Select Bond", sheet_names)
    df = data[bond_choice]

    st.title("Infrastructure Bond Calculator")
    face_value = st.number_input("Enter Face Value", min_value=1000, step=1000, value=1000000)
    trade_date = st.date_input("Trade Date", datetime.today())

    if st.button("Calculate"):
        results = calculate_consideration(df, face_value, pd.to_datetime(trade_date))
        st.subheader("Client View")
        st.write("**Face Value:**", results["face_value"])
        st.write("**Dirty Price:**", results["dirty_price"])
        st.write("**Accrued Interest:**", results["accrued_interest"])
        st.write("**Charges/Fees:**", results["charges"])
        st.write("**Consideration (Total Payment):**", results["consideration"])

        st.subheader("Cashflow Schedule")
        st.dataframe(results["cashflows"])

if __name__ == "__main__":
    main()
