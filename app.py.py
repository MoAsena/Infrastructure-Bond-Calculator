import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
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
            'nominal': 100  # Default nominal value
        }
        
        # Search for key bond information
        for row in range(min(30, df.shape[0])):  # Check first 30 rows
            for col in range(min(10, df.shape[1])):  # Check first 10 columns
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
                        bond_data['issue_date'] = df.iat[row, col+1]
                    except:
                        pass
        
        # Estimate maturity years from sheet name if possible
        try:
            # Try to extract maturity from sheet name (e.g., IFB1.2018.15 -> 15 years)
            parts = sheet_name.split('.')
            if len(parts) >= 3:
                bond_data['maturity_years'] = float(parts[-1])
        except:
            pass
        
        bond_info[sheet_name] = bond_data
    
    return bond_info

# Function to calculate bond cash flows and consideration
def calculate_bond_cashflows(bond_data, face_value, trade_date=None):
    if trade_date is None:
        trade_date = datetime.now().date()
    
    # Extract bond parameters
    coupon_rate = bond_data['coupon_rate'] / 100
    maturity_years = bond_data['maturity_years']
    ytm = bond_data['yield_to_maturity'] / 100
    issue_date = bond_data.get('issue_date', trade_date)
    
    # If issue_date is a string, try to convert to datetime
    if isinstance(issue_date, str):
        try:
            issue_date = datetime.strptime(issue_date.split()[0], '%Y-%m-%d')
        except:
            issue_date = trade_date
    
    # Calculate number of payment periods (semi-annual)
    payment_frequency = 2
    total_periods = int(maturity_years * payment_frequency)
    
    # Calculate periodic coupon payment
    periodic_coupon = (face_value * coupon_rate) / payment_frequency
    
    # Generate cash flow dates
    cashflow_dates = []
    current_date = issue_date
    
    # If issue_date is datetime, use it directly
    if isinstance(issue_date, datetime):
        current_date = issue_date
    else:
        current_date = datetime.combine(issue_date, datetime.min.time())
    
    for period in range(1, total_periods + 1):
        months_to_add = 12 / payment_frequency
        current_date = current_date + timedelta(days=30 * months_to_add)
        cashflow_dates.append(current_date)
    
    # Calculate present value of each cash flow
    cashflows = []
    present_values = []
    
    for i, date in enumerate(cashflow_dates):
        if i == len(cashflow_dates) - 1:
            # Last payment includes face value
            cashflow = periodic_coupon + face_value
        else:
            cashflow = periodic_coupon
        
        period_num = i + 1
        # Calculate time to payment in years from trade date
        time_to_payment = (date - trade_date).days / 365.25
        
        # Only include future cash flows
        if time_to_payment > 0:
            discount_factor = 1 / ((1 + ytm) ** time_to_payment)
            pv = cashflow * discount_factor
            
            cashflows.append({
                'Period': period_num,
                'Date': date.strftime('%Y-%m-%d'),
                'Cash Flow': cashflow,
                'Time to Payment (Years)': time_to_payment,
                'Discount Factor': discount_factor,
                'Present Value': pv
            })
            present_values.append(pv)
    
    # Total consideration is sum of all present values
    consideration = sum(present_values) if present_values else 0
    
    return pd.DataFrame(cashflows), consideration

# Function to get net amounts (from your original code)
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

# Main application
def main():
    st.markdown('<h1 class="main-header">🏗️ Infrastructure Bond Calculator</h1>', unsafe_allow_html=True)
    
    # File upload section
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Upload Bond Data File")
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"], help="Upload the Infrastructure Bonds Excel file")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        try:
            # Extract bond information from the Excel file
            bond_info = extract_bond_info(uploaded_file)
            
            # Create two columns layout
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Bond Selection & Parameters")
                
                # Bond selection
                bond_names = list(bond_info.keys())
                selected_bond = st.selectbox(
                    "Select Bond:",
                    options=bond_names,
                    index=0,
                    help="Choose the bond you want to analyze"
                )
                
                # Display bond details
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
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Face value input
                face_value = st.number_input(
                    "Face Value (KES):",
                    min_value=1000,
                    max_value=100000000,
                    value=100000,
                    step=1000,
                    help="Enter the face value of the bond"
                )
                
                # Trade date input
                trade_date = st.date_input(
                    "Trade Date:",
                    value=datetime.now().date(),
                    help="Select the trade date for valuation"
                )
                
                # Calculate button
                calculate_btn = st.button("Calculate Consideration & Cash Flows", type="primary", use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                if calculate_btn:
                    with st.spinner("Calculating bond valuation..."):
                        try:
                            # Calculate cash flows and consideration
                            cashflows_df, consideration = calculate_bond_cashflows(
                                bond_data, face_value, trade_date
                            )
                            
                            # Display results
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
                            
                            # Display cash flows table if available
                            if not cashflows_df.empty:
                                st.subheader("📅 Cash Flow Schedule")
                                
                                # Format the cashflow table
                                formatted_df = cashflows_df.copy()
                                formatted_df['Cash Flow'] = formatted_df['Cash Flow'].apply(lambda x: f"KES {x:,.2f}")
                                formatted_df['Present Value'] = formatted_df['Present Value'].apply(lambda x: f"KES {x:,.2f}")
                                formatted_df['Discount Factor'] = formatted_df['Discount Factor'].apply(lambda x: f"{x:.4f}")
                                formatted_df['Time to Payment (Years)'] = formatted_df['Time to Payment (Years)'].apply(lambda x: f"{x:.2f}")
                                
                                st.dataframe(
                                    formatted_df,
                                    use_container_width=True,
                                    hide_index=True
                                )
                                
                                # Cash flow visualization
                                st.subheader("📊 Cash Flow Visualization")
                                
                                # Create a bar chart of cash flows
                                fig = px.bar(
                                    cashflows_df,
                                    x='Period',
                                    y='Cash Flow',
                                    title='Cash Flow by Period',
                                    labels={'Cash Flow': 'Amount (KES)', 'Period': 'Payment Period'}
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Create a line chart of present values
                                fig2 = px.line(
                                    cashflows_df,
                                    x='Period',
                                    y='Present Value',
                                    title='Present Value by Period',
                                    labels={'Present Value': 'Amount (KES)', 'Period': 'Payment Period'}
                                )
                                st.plotly_chart(fig2, use_container_width=True)
                                
                                # Download button for cash flows
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
            
            # Show net amounts from all sheets
            st.markdown("---")
            st.subheader("Net Amounts from All Bond Sheets")
            
            try:
                net_amounts = get_net_amounts(uploaded_file)
                net_df = pd.DataFrame(list(net_amounts.items()), columns=["Bond Sheet", "Net Amount Payable"])
                
                # Format net amounts
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
        # Show instructions when no file is uploaded
        st.info("Please upload an Excel file to begin analyzing infrastructure bonds.")
        
        # Instructions section
        st.markdown("---")
        st.subheader("ℹ️ How to Use This Calculator")
        st.write("""
        1. **Upload an Excel file** containing infrastructure bond data
        2. **Select a bond** from the dropdown list (sheets from your Excel file)
        3. **Enter the face value** you want to analyze
        4. **Select the trade date** for valuation
        5. Click **"Calculate Consideration & Cash Flows"** to see results
        6. View the detailed cash flow schedule and visualizations
        7. Download the cash flow data if needed
        """)
        
        # Sample bond data for demonstration
        st.markdown("---")
        st.subheader("📋 Sample Bond Structure")
        sample_data = {
            'Bond Name': ['IFB1.2018.15', 'IFB1.2023.17', 'IFB1.2023.07', 'IFB1.2023.6.5', 'IFB1.2024.8.5'],
            'Coupon Rate': [12.5, 14.4, 15.8, 17.9, 18.5],
            'Maturity (Years)': [15, 17, 7, 6.5, 8.5],
            'Yield to Maturity': [12.0, 12.0, 11.5, 13.5, 13.1]
        }
        st.dataframe(pd.DataFrame(sample_data), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()