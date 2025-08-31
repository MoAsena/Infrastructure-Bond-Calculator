import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import plotly.express as px
from io import BytesIO

# Set page configuration
st.set_page_config(
    page_title="Infrastructure Bond Calculator",
    page_icon="📈",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 20px;
    }
    .result-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 8px;
        border: 2px solid #1f77b4;
    }
    .bond-info {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

def safe_date_conversion(date_val):
    """Safely convert various date formats to datetime.date"""
    if pd.isna(date_val):
        return None
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, str):
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    return datetime.strptime(date_val.split()[0], fmt).date()
                except:
                    continue
        except:
            return None
    if isinstance(date_val, (int, float)):
        # Handle Excel serial dates
        try:
            return datetime(1899, 12, 30) + timedelta(days=int(date_val))
        except:
            return None
    return None

# Function to extract bond information from Excel sheets
def extract_bond_info(file):
    xls = pd.ExcelFile(file)
    bond_info = {}
    
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet_name, header=None)
        
        # Initialize bond data dictionary
        bond_data = {
            'name': sheet_name,
            'coupon_rate': None,
            'maturity_years': None,
            'issue_date': None,
            'yield_to_maturity': None,
            'nominal': 100,
            'cashflow_dates': [],
            'cashflow_amounts': []
        }
        
        # Search for key bond information
        for row in range(min(30, df.shape[0])):
            for col in range(min(10, df.shape[1])):
                cell_value = str(df.iat[row, col]).strip().lower()
                
                # Find coupon rate
                if 'coupon rate' in cell_value and bond_data['coupon_rate'] is None:
                    try:
                        bond_data['coupon_rate'] = float(df.iat[row, col+1]) * 100
                    except:
                        pass
                
                # Find yield to maturity
                if ('yield' in cell_value and 'maturity' in cell_value) and bond_data['yield_to_maturity'] is None:
                    try:
                        bond_data['yield_to_maturity'] = float(df.iat[row, col+1]) * 100
                    except:
                        pass
                
                # Find issue date
                if 'issue date' in cell_value and bond_data['issue_date'] is None:
                    try:
                        issue_date_val = df.iat[row, col+1]
                        bond_data['issue_date'] = safe_date_conversion(issue_date_val)
                    except:
                        pass
        
        # Estimate maturity years from sheet name if possible
        try:
            parts = sheet_name.split('.')
            if len(parts) >= 3:
                bond_data['maturity_years'] = float(parts[-1])
        except:
            pass
        
        # Extract cash flow data from the sheet
        bond_data = extract_cashflow_data(df, bond_data)
        
        bond_info[sheet_name] = bond_data
    
    return bond_info

def extract_cashflow_data(df, bond_data):
    """Extract cash flow dates and amounts from the Excel sheet structure"""
    cashflow_dates = []
    cashflow_amounts = []
    
    # Look for cash flow headers in different possible columns
    cashflow_columns = {
        'dates': None,
        'amounts': None
    }
    
    # Search for cash flow related headers
    for row in range(min(20, df.shape[0])):
        for col in range(min(15, df.shape[1])):
            cell_value = str(df.iat[row, col]).strip().lower()
            
            if 'cash flow dates' in cell_value:
                cashflow_columns['dates'] = col
            elif 'cash flows' in cell_value and cashflow_columns['amounts'] is None:
                cashflow_columns['amounts'] = col
            elif 'cash flow' in cell_value and cashflow_columns['amounts'] is None:
                cashflow_columns['amounts'] = col
    
    # If we found the columns, extract the data
    if cashflow_columns['dates'] is not None and cashflow_columns['amounts'] is not None:
        date_col = cashflow_columns['dates']
        amount_col = cashflow_columns['amounts']
        
        # Extract dates and amounts starting from the row below the header
        start_row = None
        for row in range(min(20, df.shape[0])):
            if str(df.iat[row, date_col]).strip().lower() == 'cash flow dates':
                start_row = row + 1
                break
        
        if start_row is None:
            start_row = 6  # Default start row based on your Excel structure
        
        # Extract data
        for row in range(start_row, min(start_row + 50, df.shape[0])):
            try:
                date_val = df.iat[row, date_col]
                amount_val = df.iat[row, amount_col]
                
                if pd.isna(date_val) or pd.isna(amount_val):
                    continue
                
                # Convert date
                date_obj = safe_date_conversion(date_val)
                if date_obj is None:
                    continue
                
                # Convert amount to float
                try:
                    amount_float = float(amount_val)
                    if amount_float != 0:
                        cashflow_dates.append(date_obj)
                        cashflow_amounts.append(amount_float)
                except (ValueError, TypeError):
                    continue
                    
            except (IndexError, ValueError):
                continue
    
    bond_data['cashflow_dates'] = cashflow_dates
    bond_data['cashflow_amounts'] = cashflow_amounts
    return bond_data

# Function to calculate bond cash flows and consideration using extracted data
def calculate_bond_cashflows(bond_data, face_value, trade_date=None):
    if trade_date is None:
        trade_date = datetime.now().date()
    
    # Use the pre-extracted cash flow data
    cashflow_dates = bond_data.get('cashflow_dates', [])
    cashflow_amounts = bond_data.get('cashflow_amounts', [])
    
    # Extract bond parameters
    ytm = bond_data.get('yield_to_maturity', 0) / 100
    
    # If no cash flows were extracted, try to generate them from bond parameters
    if not cashflow_dates:
        return generate_cashflows_from_params(bond_data, face_value, trade_date, ytm)
    
    # Calculate present value of each cash flow
    cashflows = []
    present_values = []
    
    for i, (cf_date, amount) in enumerate(zip(cashflow_dates, cashflow_amounts)):
        # Calculate time to payment in years from trade date
        if cf_date and isinstance(cf_date, date):
            time_to_payment = (cf_date - trade_date).days / 365.25
            
            # Only include future cash flows
            if time_to_payment > 0:
                discount_factor = 1 / ((1 + ytm) ** time_to_payment)
                pv = amount * discount_factor
                
                cashflows.append({
                    'Period': i + 1,
                    'Date': cf_date.strftime('%Y-%m-%d'),
                    'Cash Flow': amount,
                    'Time to Payment (Years)': time_to_payment,
                    'Discount Factor': discount_factor,
                    'Present Value': pv
                })
                present_values.append(pv)
    
    # Total consideration is sum of all present values
    consideration = sum(present_values) if present_values else 0
    
    return pd.DataFrame(cashflows), consideration

def generate_cashflows_from_params(bond_data, face_value, trade_date, ytm):
    """Generate cash flows from bond parameters if extraction fails"""
    coupon_rate = bond_data.get('coupon_rate', 0) / 100
    maturity_years = bond_data.get('maturity_years', 0)
    issue_date = bond_data.get('issue_date', trade_date)
    
    # Calculate number of payment periods (semi-annual)
    payment_frequency = 2
    total_periods = int(maturity_years * payment_frequency)
    
    # Calculate periodic coupon payment
    periodic_coupon = (face_value * coupon_rate) / payment_frequency
    
    # Generate cash flow dates
    cashflow_dates = []
    current_date = issue_date
    
    for period in range(1, total_periods + 1):
        months_to_add = 6  # Semi-annual payments
        next_date = current_date + timedelta(days=30 * months_to_add)
        cashflow_dates.append(next_date)
        current_date = next_date
    
    # Calculate present value of each cash flow
    cashflows = []
    present_values = []
    
    for i, date_val in enumerate(cashflow_dates):
        if i == len(cashflow_dates) - 1:
            cashflow = periodic_coupon + face_value
        else:
            cashflow = periodic_coupon
        
        time_to_payment = (date_val - trade_date).days / 365.25
        
        if time_to_payment > 0:
            discount_factor = 1 / ((1 + ytm) ** time_to_payment)
            pv = cashflow * discount_factor
            
            cashflows.append({
                'Period': i + 1,
                'Date': date_val.strftime('%Y-%m-%d'),
                'Cash Flow': cashflow,
                'Time to Payment (Years)': time_to_payment,
                'Discount Factor': discount_factor,
                'Present Value': pv
            })
            present_values.append(pv)
    
    consideration = sum(present_values) if present_values else 0
    return pd.DataFrame(cashflows), consideration

# Function to get net amounts
def get_net_amounts(file):
    xls = pd.ExcelFile(file)
    results = {}

    for sheet in xls.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet, header=None)
        found = False
        
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                if str(df.iat[row, col]).strip().lower() == "net amount payable":
                    try:
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

# Main application
def main():
    st.markdown('<h1 class="main-header">🏗️ Infrastructure Bond Calculator</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Upload Bond Data File")
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"], help="Upload the Infrastructure Bonds Excel file")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        try:
            bond_info = extract_bond_info(uploaded_file)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Bond Selection & Parameters")
                
                bond_names = list(bond_info.keys())
                selected_bond = st.selectbox(
                    "Select Bond:",
                    options=bond_names,
                    index=0,
                    help="Choose the bond you want to analyze"
                )
                
                st.markdown('<div class="bond-info">', unsafe_allow_html=True)
                st.write(f"**Bond Name:** {selected_bond}")
                
                bond_data = bond_info[selected_bond]
                if bond_data['coupon_rate']:
                    st.write(f"**Coupon Rate:** {bond_data['coupon_rate']:.2f}%")
                if bond_data['yield_to_maturity']:
                    st.write(f"**Yield to Maturity:** {bond_data['yield_to_maturity']:.2f}%")
                if bond_data['maturity_years']:
                    st.write(f"**Maturity:** {bond_data['maturity_years']} years")
                if bond_data['issue_date']:
                    st.write(f"**Issue Date:** {bond_data['issue_date']}")
                
                st.write(f"**Extracted Cash Flows:** {len(bond_data['cashflow_dates'])} payments found")
                st.markdown('</div>', unsafe_allow_html=True)
                
                face_value = st.number_input(
                    "Face Value (KES):",
                    min_value=1000,
                    max_value=100000000,
                    value=100000,
                    step=1000,
                    help="Enter the face value of the bond"
                )
                
                trade_date = st.date_input(
                    "Trade Date:",
                    value=datetime.now().date(),
                    help="Select the trade date for valuation"
                )
                
                calculate_btn = st.button("Calculate Consideration & Cash Flows", type="primary", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                if calculate_btn:
                    with st.spinner("Calculating bond valuation..."):
                        try:
                            cashflows_df, consideration = calculate_bond_cashflows(
                                bond_data, face_value, trade_date
                            )
                            
                            st.markdown('<div class="result-box">', unsafe_allow_html=True)
                            st.subheader("💰 Calculation Results")
                            
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.metric(
                                    label="Total Consideration (KES)",
                                    value=f"KES {consideration:,.2f}",
                                    help="Present value of all future cash flows"
                                )
                            
                            with col_b:
                                discount = face_value - consideration
                                discount_percent = (discount / face_value * 100) if face_value else 0
                                st.metric(
                                    label="Discount/Premium",
                                    value=f"KES {discount:,.2f}",
                                    delta=f"{discount_percent:.2f}%",
                                    help="Difference between face value and consideration"
                                )
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            if not cashflows_df.empty:
                                st.subheader("📅 Cash Flow Schedule")
                                
                                formatted_df = cashflows_df.copy()
                                formatted_df['Cash Flow'] = formatted_df['Cash Flow'].apply(lambda x: f"KES {x:,.2f}")
                                formatted_df['Present Value'] = formatted_df['Present Value'].apply(lambda x: f"KES {x:,.2f}")
                                formatted_df['Discount Factor'] = formatted_df['Discount Factor'].apply(lambda x: f"{x:.4f}")
                                formatted_df['Time to Payment (Years)'] = formatted_df['Time to Payment (Years)'].apply(lambda x: f"{x:.2f}")
                                
                                st.dataframe(formatted_df, use_container_width=True, hide_index=True)
                                
                                st.subheader("📊 Cash Flow Visualization")
                                fig = px.bar(cashflows_df, x='Period', y='Cash Flow', title='Cash Flow by Period')
                                st.plotly_chart(fig, use_container_width=True)
                                
                                csv = cashflows_df.to_csv(index=False)
                                st.download_button(
                                    label="Download Cash Flow Schedule as CSV",
                                    data=csv,
                                    file_name=f"cashflows_{selected_bond.replace(' ', '_')}.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.warning("No future cash flows found for the selected trade date.")
                                
                        except Exception as e:
                            st.error(f"Error calculating bond valuation: {str(e)}")
            
            st.markdown("---")
            st.subheader("Net Amounts from All Bond Sheets")
            
            try:
                net_amounts = get_net_amounts(uploaded_file)
                net_df = pd.DataFrame(list(net_amounts.items()), columns=["Bond Sheet", "Net Amount Payable"])
                
                def format_net_amount(x):
                    if isinstance(x, (int, float)):
                        return f"KES {x:,.2f}"
                    return x
                
                net_df['Net Amount Payable'] = net_df['Net Amount Payable'].apply(format_net_amount)
                st.dataframe(net_df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Error extracting net amounts: {str(e)}")
                
        except Exception as e:
            st.error(f"Error processing the Excel file: {str(e)}")
    
    else:
        st.info("Please upload an Excel file to begin analyzing infrastructure bonds.")
        
        st.markdown("---")
        st.subheader("ℹ️ How to Use This Calculator")
        st.write("""
        1. **Upload an Excel file** containing infrastructure bond data
        2. **Select a bond** from the dropdown list
        3. **Enter the face value** you want to analyze
        4. **Select the trade date** for valuation
        5. Click **"Calculate Consideration & Cash Flows"** to see results
        6. View the detailed cash flow schedule and visualizations
        """)

if __name__ == "__main__":
    main()