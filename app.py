import pandas as pd
import streamlit as st

def get_net_amounts(file):
    xls = pd.ExcelFile(file)
    results = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet, header=None)

        # Search each cell for the text "Net Amount Payable"
        found = False
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                if str(df.iat[row, col]).strip().lower() == "net amount payable":
                    try:
                        # Assume value is one cell to the right
                        value = df.iat[row, col + 1]
                        results[sheet] = value
                        found = True
                        break
                    except:
                        results[sheet] = "Value not found"
                        found = True
                        break
            if found:
                break

        if not found:
            results[sheet] = "Not found"

    return results

def main():
    st.title("Infrastructure Bond Calculator")

    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        net_amounts = get_net_amounts(uploaded_file)

        st.subheader("Net Amount Payable from Each Sheet")
        st.write(pd.DataFrame(list(net_amounts.items()), columns=["Sheet", "Net Amount Payable"]))

if __name__ == "__main__":
    main()
