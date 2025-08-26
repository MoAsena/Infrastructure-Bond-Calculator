import streamlit as st
import pandas as pd

# Map each sheet to its consideration cell location
CONSIDERATION_CELLS = {
    "IFB1.2018.15": (21, 0),  # A22
    "IFB1.2023.17": (23, 0),  # A24
    "IFB1.2023.07": (22, 0),  # A23
    "IFB1.2023.6.5": (23, 1), # B24
    "IFB1.2024.8.5": (22, 1), # B23
}

def load_data(sheet_name):
    df = pd.read_excel("Infrastruture Bonds.xlsx", sheet_name=sheet_name, header=None)

    # Get consideration from defined cell
    if sheet_name in CONSIDERATION_CELLS:
        row, col = CONSIDERATION_CELLS[sheet_name]
        consideration = df.iloc[row, col]
    else:
        consideration = None

    # Extract cashflows (from row 30 onward: index 29)
    cashflows = df.iloc[29:, [0, 1]].dropna()
    cashflows.columns = ["Date", "Amount"]

    return consideration, cashflows

def main():
    st.title("Infrastructure Bond Calculator")

    # File uploader
    uploaded_file = st.file_uploader("Upload Infrastructure Bonds Excel file", type=["xlsx"])
    if uploaded_file is None:
        st.info("Please upload an Excel file to proceed.")
        return

    # Read Excel and allow sheet selection
    xls = pd.ExcelFile(uploaded_file)
    sheet_name = st.selectbox("Select Bond Sheet", xls.sheet_names)

    consideration, cashflows = load_data(sheet_name)

    st.subheader("Bond Details")
    st.write(f"**Trade Date**: {pd.Timestamp.now().date()}")
    st.write(f"**Consideration**: {consideration:,}" if consideration else "Consideration not found")

    # Fees and levies calculation
    if consideration:
        brokerage_comm = 1000
        other_levies = 0.00035 * consideration
        general_fees = max(brokerage_comm + other_levies, 0.00035 * consideration)
        vat = 0.16 * brokerage_comm
        total_charges = brokerage_comm + other_levies + vat

        st.subheader("Charges Summary")
        st.write(f"Brokerage Commission: {brokerage_comm:,.2f}")
        st.write(f"Other Levies: {other_levies:,.2f}")
        st.write(f"VAT on Brokerage: {vat:,.2f}")
        st.write(f"**Total Charges: {total_charges:,.2f}**")

    # Show cashflows
    st.subheader("Cashflows")
    st.dataframe(cashflows)

if __name__ == "__main__":
    main()
