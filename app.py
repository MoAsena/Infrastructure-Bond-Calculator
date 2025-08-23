
import os
import math
from datetime import date
import pandas as pd
import numpy as np
import streamlit as st

EXCEL_PATH_DEFAULT = "Infrastruture Bonds.xlsx"

st.set_page_config(page_title="Bond Consideration (5 Bonds)", page_icon="💹", layout="wide")

# ---------- Helpers ----------
@st.cache_data(show_spinner=False)
def load_workbook(path_or_buffer):
    try:
        xls = pd.ExcelFile(path_or_buffer)
        return xls, xls.sheet_names
    except Exception as e:
        return None, []

def scan_labels(df, max_rows=120, max_cols=16):
    labels = {}
    for r in range(min(max_rows, df.shape[0])):
        for c in range(min(max_cols, df.shape[1])):
            cell = df.iat[r, c]
            if isinstance(cell, str) and cell.strip().endswith(':'):
                key = cell.strip()[:-1]
                # find first non-NaN to the right
                val = None
                for cc in range(c+1, min(c+6, df.shape[1])):
                    vv = df.iat[r, cc]
                    if pd.notna(vv):
                        val = vv
                        break
                labels[key] = val
    return labels

def extract_cashflows(df):
    best = None
    for col in range(df.shape[1]):
        try:
            dates = pd.to_datetime(df.iloc[:, col], errors="coerce")
        except Exception:
            dates = pd.Series([pd.NaT]*len(df))
        if dates.notna().sum() >= 3:
            for ac in range(col+1, min(col+6, df.shape[1])):
                amounts = pd.to_numeric(df.iloc[:, ac], errors="coerce")
                if amounts.notna().sum() >= 3 and amounts.abs().max() > 0:
                    cf = pd.DataFrame({"Date": dates, "Amount": amounts})
                    cf = cf.dropna(subset=["Date", "Amount"])
                    cf = cf[cf["Amount"] != 0]
                    if 1 <= len(cf) <= 500:
                        return cf.sort_values("Date").reset_index(drop=True)
    return best

def years_act365(d1, d2):
    return (pd.Timestamp(d2) - pd.Timestamp(d1)).days / 365.0

def ytm_from_cashflows(settlement_date, dirty_price_per_100, cashflows, guess=0.12, tol=1e-8, max_iter=100):
    # Solve for simple annual compounding IRR: sum(cf/(1+y)**t) = dirty_price_per_100
    times = np.array([max(0.0, years_act365(settlement_date, d)) for d in cashflows["Date"]], dtype=float)
    cfs = cashflows["Amount"].to_numpy(dtype=float)
    # scale PV to per-100 basis
    target = dirty_price_per_100

    y = guess
    for _ in range(max_iter):
        denom = (1.0 + y) ** times
        pv = np.sum(cfs / denom)
        # derivative wrt y
        dpv = np.sum(-times * cfs / ((1.0 + y) ** (times + 1e-16)))
        err = pv - target
        if abs(err) < tol:
            return max(-0.9999, y)
        # guard
        if dpv == 0:
            break
        y = y - err / dpv
        if not np.isfinite(y) or y <= -0.99:
            y = max(1e-6, guess)
    return max(-0.9999, y)

def compute_fees(gross_amount):
    # Hidden backend fee model (adjust as needed)
    commission_rate = 0.0010  # 0.10%
    vat_rate = 0.16           # 16% on commission
    nse = 0.0
    cdsc = 0.0
    cma = 0.0
    commission = commission_rate * gross_amount
    vat = vat_rate * commission
    total_fees = commission + vat + nse + cdsc + cma
    return total_fees

# ---------- Load Excel ----------
st.sidebar.header("Data Source")
default_available = os.path.exists(EXCEL_PATH_DEFAULT)
data_choice = st.sidebar.radio("Source", ["Use file in repo", "Upload"], index=0 if default_available else 1)

xls = None
sheet_names = []
if data_choice == "Use file in repo":
    if default_available:
        xls, sheet_names = load_workbook(EXCEL_PATH_DEFAULT)
    else:
        st.sidebar.error(f"'{EXCEL_PATH_DEFAULT}' not found in app folder. Please upload below.")
else:
    uploaded = st.sidebar.file_uploader("Upload 'Infrastruture Bonds.xlsx'", type=["xlsx"])
    if uploaded:
        xls, sheet_names = load_workbook(uploaded)

if not sheet_names:
    st.info("Load the workbook to proceed. Expecting 5 sheets (one per bond).")
    st.stop()

# ---------- UI: Bond selection ----------
bond_name = st.sidebar.selectbox("Select Bond", sheet_names)

df_raw = pd.read_excel(xls, sheet_name=bond_name, header=None)
labels = scan_labels(df_raw)
cashflows = extract_cashflows(df_raw)

# Pull core fields (with safe defaults)
issue_date = pd.to_datetime(labels.get("Issue Date", pd.NaT), errors="coerce")
maturity_date = pd.to_datetime(labels.get("Maturity Date", pd.NaT), errors="coerce")
coupon_rate = labels.get("Coupon Rate", np.nan)  # e.g., 0.125
dirty_price = labels.get("Dirty Price", np.nan)  # per 100
clean_price = labels.get("Clean Price", np.nan)  # per 100
accrued_pct = labels.get("Accrued Interest", np.nan)  # per 100
ytm_sheet = labels.get("Yield To Maturity", np.nan)

# ---------- Client Inputs (limited view) ----------
st.title("💹 Bond Consideration Calculator")
colA, colB, colC = st.columns(3)
with colA:
    face_value = st.number_input("Face Value (KES)", min_value=1000.0, value=10_000_000.0, step=100_000.0, format="%.2f")
with colB:
    trade_date = st.date_input("Trade Date", value=pd.Timestamp.today().date())
with colC:
    value_date = st.date_input("Value/Settlement Date", value=pd.Timestamp.today().date())

# ---------- Compute backend metrics ----------
# If dirty price missing, recompute from clean+accrued
if pd.isna(dirty_price) and pd.notna(clean_price) and pd.notna(accrued_pct):
    dirty_price = float(clean_price) + float(accrued_pct)

# Compute YTM quietly in background if possible
ytm_est = None
if cashflows is not None and pd.notna(dirty_price):
    try:
        ytm_est = ytm_from_cashflows(value_date, float(dirty_price), cashflows, guess=float(ytm_sheet) if pd.notna(ytm_sheet) else 0.12)
    except Exception:
        ytm_est = float(ytm_sheet) if pd.notna(ytm_sheet) else None

# Gross (dirty) cash amount
gross_amount = (float(dirty_price) / 100.0) * face_value if pd.notna(dirty_price) else np.nan
fees_hidden = compute_fees(gross_amount) if np.isfinite(gross_amount) else np.nan
consideration = gross_amount + fees_hidden if np.isfinite(gross_amount) else np.nan

# ---------- Client View ----------
top = st.columns(4)
top[0].metric("Selected Bond", bond_name)
top[1].metric("Dirty Price (% of Face)", f"{dirty_price:,.6f}" if pd.notna(dirty_price) else "N/A")
top[2].metric("Trade Date", str(trade_date))
top[3].metric("Value Date", str(value_date))

st.subheader("Cashflow Schedule")
if cashflows is not None and not cashflows.empty:
    cf_show = cashflows.copy()
    cf_show["Date"] = cf_show["Date"].dt.date
    cf_show["Amount"] = cf_show["Amount"].round(2)
    st.dataframe(cf_show, use_container_width=True, hide_index=True)
else:
    st.info("No cashflows detected on this sheet.")

st.subheader("Client Summary")
summary = pd.DataFrame({
    "Field": ["Face Value (KES)", "Dirty Price (%)", "Consideration (KES)", "Trade Date", "Value Date"],
    "Value": [
        f"{face_value:,.2f}",
        f"{dirty_price:,.6f}" if pd.notna(dirty_price) else "N/A",
        f"{consideration:,.2f}" if np.isfinite(consideration) else "N/A",
        str(trade_date),
        str(value_date),
    ],
})
st.dataframe(summary, use_container_width=True, hide_index=True)

# (We intentionally do NOT display fees or YTM here per requirements.)

# Download cashflows
if cashflows is not None and not cashflows.empty:
    st.download_button("Download Cashflows (CSV)", data=cashflows.to_csv(index=False).encode("utf-8"),
                       file_name=f"{bond_name}_cashflows.csv", mime="text/csv")
