import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# Function to calculate Dirty Price and Consideration
def calculate_dirty_price_and_consideration(coupon_rate, ytm, nominal, trade_date, maturity_date):
    """
    Calculates the dirty price and consideration for a bond.
    """
    # This is a simplified calculation and may not match the provided data exactly due to
    # the complexity of actual bond pricing models.
    # It demonstrates the link between a backend calculation and frontend input.

    # Time to maturity in years (approximate)
    time_to_maturity = (maturity_date - trade_date).days / 365.25
    
    # Present Value of future cash flows (simplified)
    # This part of the code would need to be replaced with a more robust bond pricing model
    # to accurately replicate the provided data's calculations.
    pv_of_coupons = 0
    pv_of_principal = nominal / (1 + ytm)**time_to_maturity
    
    # For simplicity, we are not calculating each cash flow, but you can expand this section
    # to iterate through each cash flow date as shown in the original files.
    
    # Dirty Price is the sum of PV of future cash flows.
    dirty_price = pv_of_coupons + pv_of_principal

    # Accrued Interest Calculation (Simplified)
    # The actual accrued interest calculation is more complex and depends on
    # day count conventions (e.g., actual/actual, 30/360).
    days_in_period = 182.625 # Semi-annual
    days_since_last_payment = (trade_date - pd.to_datetime('2025-07-21')).days # Using a known date from a file
    accrued_interest = (coupon_rate * nominal / 2) * (days_since_last_payment / days_in_period)

    clean_price = dirty_price - accrued_interest
    
    consideration = dirty_price * nominal
    
    return dirty_price, accrued_interest, clean_price, consideration

# Function to calculate all cash flows based on a new face value
def calculate_cashflows(face_value, issue_number):
    """
    Simulates the backend logic to generate cash flows based on a given face value.
    The values and dates are hardcoded for demonstration purposes and should be
    replaced with a more dynamic data retrieval system in a real application.
    """
    cashflows = []
    
    if issue_number == 'IFB1/2018/15':
        # [cite_start]This data is taken directly from the source file [cite: 1]
        dates = pd.to_datetime(['2026-01-19', '2026-07-20', '2027-01-18', '2027-07-19', '2028-01-17', '2028-01-17'])
        original_face_value = 500000.0
        original_cashflows = [31250, 31250, 31250, 31250, 31250, 500000]
        
        # Scale the original cash flows based on the new face value
        cashflows = [cf * (face_value / original_face_value) for cf in original_cashflows]
        
        # Combine dates and scaled cash flows into a DataFrame
        df = pd.DataFrame({
            'Date': dates,
            'Cash Flow Amount (KES)': cashflows
        })
        return df
    
    elif issue_number == 'IFB1/2023/17':
        # [cite_start]Data from source [cite: 2]
        dates = pd.to_datetime(['2025-09-08', '2026-03-09', '2026-09-07', '2027-03-08', '2027-09-06', '2028-03-06'])
        original_face_value = 500000.0
        original_cashflows = [35997.5, 35997.5, 35997.5, 35997.5, 35997.5, 35997.5]
        
        cashflows = [cf * (face_value / original_face_value) for cf in original_cashflows]
        df = pd.DataFrame({
            'Date': dates,
            'Cash Flow Amount (KES)': cashflows
        })
        return df

    elif issue_number == 'IFB1/2023/7':
        # [cite_start]Data from source [cite: 3]
        dates = pd.to_datetime(['2025-06-16', '2025-12-15', '2026-06-15', '2026-06-15', '2026-12-14', '2027-06-14', '2027-12-13', '2027-12-13', '2028-06-12'])
        [cite_start]original_face_value = 500000.0 # From the cashflow header [cite: 3]
        original_cashflows = [158370, 158370, 158370, 400000, 126696, 126696, 126696, 480000, 88687.2]
        
        cashflows = [cf * (face_value / original_face_value) for cf in original_cashflows]
        df = pd.DataFrame({
            'Date': dates,
            'Cash Flow Amount (KES)': cashflows
        })
        return df

    elif issue_number == 'IFB1/2023/6.5':
        # [cite_start]Data from source [cite: 4]
        dates = pd.to_datetime(['2025-11-10', '2026-05-11', '2026-11-09', '2027-05-10', '2027-05-10'])
        original_nominal = 100.0
        # The cashflows need to be scaled by the face value, which is not provided, so we
        # use the nominal value as a basis for calculation.
        original_cashflows = [8.9663499999999985, 8.9663499999999985, 8.9663499999999985, 8.9663499999999985, 50.0]
        
        # Scale the original cash flows based on the new face value. Since a specific face value is
        # [cite_start]not given, we will scale based on the nominal value of 100 from the source [cite: 4]
        cashflows = [cf * (face_value / original_nominal) for cf in original_cashflows]
        df = pd.DataFrame({
            'Date': dates,
            'Cash Flow Amount (KES)': cashflows
        })
        return df
        
    elif issue_number == 'IFB1/2024/8.5':
        # [cite_start]Data from source [cite: 5]
        dates = pd.to_datetime(['2025-08-18', '2026-02-16', '2026-08-17', '2027-02-15', '2027-02-15'])
        original_nominal = 100.0
        original_cashflows = [9.23035, 9.23035, 9.23035, 9.23035, 20.0]
        
        cashflows = [cf * (face_value / original_nominal) for cf in original_cashflows]
        df = pd.DataFrame({
            'Date': dates,
            'Cash Flow Amount (KES)': cashflows
        })
        return df
        
    return pd.DataFrame()

# Streamlit App Front End
st.title('Infrastructure Bond Pricing')

# Dropdown to select bond
issue_number = st.selectbox(
    'Select Bond Issue Number:',
    ['IFB1/2018/15', 'IFB1/2023/17', 'IFB1/2023/7', 'IFB1/2023/6.5', 'IFB1/2024/8.5']
)

# Hardcoded data based on selection for display
bond_data = {
    'IFB1/2018/15': {
        'Face Value': 500000.0,
        'Nominal': 100,
        'Coupon Rate': 0.125,
        'YTM': 0.12,
        'Trade Date': date(2025, 8, 30),
        'Maturity Date': date(2033, 1, 10),
        'Brokerage Rate': 0.00024,
        'Levies Rate': 0.00011,
        [cite_start]'Dirty Price': 103.1912 # Used for calculating initial consideration [cite: 1]
    },
    'IFB1/2023/17': {
        'Face Value': 500000.0,
        'Nominal': 100,
        'Coupon Rate': 0.14399,
        'YTM': 0.12,
        'Trade Date': date(2025, 8, 30),
        'Maturity Date': date(2040, 2, 20),
        'Brokerage Rate': 0.00024,
        'Levies Rate': 0.00011,
        [cite_start]'Dirty Price': 120.8268 # Used for calculating initial consideration [cite: 2]
    },
    'IFB1/2023/7': {
        'Face Value': 4000000.0,
        'Nominal': 100,
        'Coupon Rate': 0.15837,
        'YTM': 0.115,
        'Trade Date': date(2025, 8, 30),
        'Maturity Date': date(2030, 6, 10),
        'Brokerage Rate': 0.00024,
        'Levies Rate': 0.00011,
        [cite_start]'Dirty Price': 114.6613 # Used for calculating initial consideration [cite: 3]
    },
    'IFB1/2023/6.5': {
        'Face Value': 50000.0,
        'Nominal': 100,
        'Coupon Rate': 0.179327,
        'YTM': 0.135,
        'Trade Date': date(2025, 8, 26),
        'Maturity Date': date(2030, 5, 6),
        'Brokerage Rate': 0.00024,
        'Levies Rate': 0.00011,
        [cite_start]'Dirty Price': 115.6068 # Used for calculating initial consideration [cite: 4]
    },
    'IFB1/2024/8.5': {
        'Face Value': 1000000.0,
        'Nominal': 100,
        'Coupon Rate': 0.184607,
        'YTM': 0.130806,
        'Trade Date': date(2025, 8, 27),
        'Maturity Date': date(2032, 8, 9),
        'Brokerage Rate': 0.00012,
        'Levies Rate': 0.00011,
        [cite_start]'Dirty Price': 119.6333 # Used for calculating initial consideration [cite: 5]
    }
}

selected_data = bond_data.get(issue_number)

if selected_data:
    st.markdown("---")
    st.subheader(f"Pricing for {issue_number}")
    
    # Sliders and number inputs for bond parameters
    face_value = st.number_input(
        'Change Face Value (KES)',
        min_value=0.0,
        value=selected_data['Face Value'],
        step=1000.0
    )
    
    # Backend calculation for Total Amount Payable
    consideration = selected_data['Dirty Price'] * face_value / selected_data['Nominal']
    brokerage_commission = consideration * selected_data['Brokerage Rate']
    transaction_levies = consideration * selected_data['Levies Rate']
    total_charges = brokerage_commission + transaction_levies
    net_amount_payable = consideration + total_charges
    
    st.markdown("---")
    st.subheader("Results")
    st.write(f"**Face Value:** KES {face_value:,.2f}")
    st.write(f"**Total Amount Payable:** KES {net_amount_payable:,.2f}")
    
    st.markdown("---")
    st.subheader("Cash Flow Details")
    
    # Backend calculation for Cash Flows
    cash_flow_df = calculate_cashflows(face_value, issue_number)
    
    if not cash_flow_df.empty:
        st.dataframe(cash_flow_df)
    else:
        st.write("No cash flow data available for this issue.")
else:
    st.error("Please select a valid bond issue number.")