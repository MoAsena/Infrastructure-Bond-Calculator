# Infrastructure Bond Calculator

This is a Streamlit app for analyzing Infrastructure Bonds from Excel sheets.  
It extracts **Consideration** values from specific cell locations and displays **cashflows** with charges summary.

## Features
- Upload the `Infrastruture Bonds.xlsx` file.
- Auto-detects Consideration from pre-defined cells for each sheet.
- Computes Brokerage commission, Other levies, VAT, and Total charges.
- Displays Cashflows (dates and amounts).

## How to Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment
You can upload this repo directly to GitHub and connect to [Streamlit Cloud](https://share.streamlit.io).
