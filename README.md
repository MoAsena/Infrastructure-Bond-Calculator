# Infrastructure Bond Calculator (Multi-Sheet)

This Streamlit app allows you to upload an Excel file with multiple sheets containing Kenyan Infrastructure Bond data.  
It extracts **Consideration**, computes **charges**, and displays **cashflows** for each mapped sheet.

## Features
- Handles multiple bond sheets (e.g., IFB1.2018.15, IFB1.2023.17, etc.).
- Extracts **Consideration** from specific cells in each sheet.
- Computes **fees** as `max(1000 + 0.035% of consideration, 0.035% of consideration)`.
- Displays a clean table of **cashflow dates and amounts**.

## How to Run
1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run app.py
   ```
3. Upload your Excel file when prompted.

## Files
- `app.py` — Main Streamlit app
- `requirements.txt` — Python dependencies
- `config.yaml` — Streamlit server config
- `README.md` — Documentation
