# Infrastructure Bond Calculator

A Streamlit web application for analyzing and calculating details of infrastructure bonds from Excel input.

## Features
- Upload and select from multiple bonds (Excel sheets).
- Display bond summary: Face Value, Consideration, Trade Date, Dirty Price.
- Automatic fee computation:
  - Brokerage commission (0.035% of consideration or minimum KES 1000)
  - Other levies (0.035% of consideration)
  - VAT (16% of brokerage commission)
  - Total charges
  - Amount payable/receivable
- Cashflow schedule (Dates & Amounts only).

## Files
- `app.py` → Main Streamlit app.
- `requirements.txt` → Python dependencies.
- `config.toml` → Streamlit configuration.
- `README.md` → Documentation.

## Usage

### 1. Local Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

### 2. Streamlit Cloud / GitHub
- Upload all files to your GitHub repository.
- Deploy on [Streamlit Cloud](https://streamlit.io/cloud).

## Excel Input
- Place `Infrastruture Bonds.xlsx` in the same directory as the app.
- Each sheet represents one bond with details: Trade Date, Consideration, Dirty Price, Coupon Rate, Frequency, Principal.

---
Author: Jane Maingi
