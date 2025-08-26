# Infrastructure Bond Calculator

This is a simple Streamlit app that extracts **Net Amount Payable** values from each sheet in an uploaded Excel file.

## Features
- Upload any Excel file (`.xlsx`).
- The app searches each sheet for the label **"Net Amount Payable"**.
- Displays the corresponding values in a clean table.

## How to Run Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

## Files
- `app.py` → Main Streamlit app.
- `requirements.txt` → Python dependencies.
- `config.yaml` → Streamlit server config.
- `README.md` → Documentation.
