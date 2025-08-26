import streamlit as st
import pandas as pd
import openpyxl

# Mapping of sheet → cell where Consideration is located
CONSIDERATION_CELLS = {
    "IFB1.2018.15": "A22",
    "IFB1.2023.17": "A24",
    "IFB1.2023.07": "A23",
    "IFB1.2023.6.5": "B24",
    "IFB1.2024.8.5": "B23"
}

def extract_from_sheet(sheet, sheet_name):
    """Extract consideration + cashflows from a single sheet"""
    results = {}

    # Get the right cell for this sheet
    cell = CONSIDERATION_CELLS.get(sheet_name)
    if not cell:
        return None  # Skip sheets not mapped

    consideration = sheet[cell].value or 0

    # Compute charges
    brokerage = 1000  # Minimum brokerage
    levies = 0.00035 * consideration
    total_charges = max(brokerage + levies, 0.00035 * consideration)
    payable = consideration + total_charges

    # --- Extract cashflows (assume start row 30, col A=date, B=amount) ---
    cashflows = []
    row = 30
    while sheet[f"A{row}"].value:
        date = sheet[f"A{row}"].value
        amount = sheet[f"B{row}"].value
        cashflows.append({"Date": date, "Amount": amount})
        row += 1

    results["Sheet"] = sheet_name
    results["Consideration"] = consideration
    results["TotalCharges"] = total_charges
    results["Payable"] = payable
    results["Cashflows"] = cashflows
    return results

def load_excel_values(file_path):
    """Loop through all mapped sheets and collect results"""
    wb = openpyxl.load_workbook(file_path, data_only=True)
    data = []
    for sheet_name in CONSIDERATION_CELLS.keys():
        if sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            result = extract_from_sheet(sheet, sheet_name)
            if result:
                data.append(result)
    return data

def main():
    st.title("Infrastructure Bond Calculator (Multi-Sheet)")

    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
    if uploaded_file:
        all_data = load_excel_values(uploaded_file)

        for entry in all_data:
            st.subheader(f"📑 Results for sheet: {entry['Sheet']}")
            st.write(f"**Consideration:** {entry['Consideration']:,.2f}")
            st.write(f"**Total Charges:** {entry['TotalCharges']:,.2f}")
            st.write(f"**Amount Payable/Receivable:** {entry['Payable']:,.2f}")

            st.markdown("**Cashflows:**")
            cf_df = pd.DataFrame(entry["Cashflows"])
            st.table(cf_df)

if __name__ == "__main__":
    main()
