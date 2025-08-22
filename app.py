

import os
import io
import yaml
import datetime as dt
import pandas as pd
import streamlit as st
from urllib.parse import urlencode
from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string

APP_TITLE = "Bond Calculator (Prototype)"
EXCEL_PATH = "Infrastruture Bonds.xlsx"
CONFIG_PATH = "config.yaml"
ADMIN_PASS = os.environ.get("ADMIN_PASS")

st.set_page_config(page_title=APP_TITLE, layout="wide")

@st.cache_resource
def load_wb():
    return load_workbook(EXCEL_PATH, data_only=False, read_only=False)

@st.cache_resource
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"sheets": {}}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    if "sheets" not in cfg:
        cfg["sheets"] = {}
    return cfg

def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)

def get_query_params():
    return st.query_params

def build_link(base_params: dict):
    qp = urlencode(base_params, doseq=True)
    return f"?{qp}" if qp else "?"

def write_inputs_to_excel(wb, sheet_name, date_val, cfg):
    if sheet_name not in cfg["sheets"]:
        return False, "No mapping for this sheet."
    s_cfg = cfg["sheets"][sheet_name]
    ws = wb[sheet_name]
    try:
        ic = s_cfg.get("input_cells", {})
        if "date" in ic and ic["date"]:
            ws[ic["date"]] = pd.to_datetime(date_val).date() if date_val else None
        return True, None
    except Exception as e:
        return False, str(e)

def read_output_table(wb, sheet_name, cfg):
    if sheet_name not in cfg["sheets"]:
        return None, "No mapping."
    s_cfg = cfg["sheets"][sheet_name]
    rng = s_cfg.get("output_range")
    if not rng:
        return None, "No output_range configured."
    ws = wb[sheet_name]
    try:
        start_cell, end_cell = rng.split(":")
        start_col = ''.join(filter(str.isalpha, start_cell))
        start_row = int(''.join(filter(str.isdigit, start_cell)))
        end_col = ''.join(filter(str.isalpha, end_cell))
        end_row = int(''.join(filter(str.isdigit, end_cell)))

        data = []
        for r in ws.iter_rows(min_row=start_row, max_row=end_row,
                              min_col=column_index_from_string(start_col),
                              max_col=column_index_from_string(end_col)):
            data.append([cell.value for cell in r])
        if data:
            header = [str(x) if x is not None else "" for x in data[0]]
            rows = data[1:]
            df = pd.DataFrame(rows, columns=header)
            return df, None
        else:
            return None, "Empty range."
    except Exception as e:
        return None, str(e)

# Load workbook & config
wb = load_wb()
cfg = load_config()
sheet_names = wb.sheetnames

# Sidebar
st.sidebar.title("Navigation")
params = get_query_params()
bond_param = params.get("bond", [None])[0] if isinstance(params.get("bond"), list) else params.get("bond")
default_sheet = bond_param if bond_param in sheet_names else sheet_names[0]
bond_choice = st.sidebar.selectbox("Select a Bond", sheet_names, index=sheet_names.index(default_sheet))
link_params = {"bond": bond_choice}
st.sidebar.markdown(f"**Direct link:** `{build_link(link_params)}`")

st.title(f"{APP_TITLE} — {bond_choice}")

# --- Client Form (only Trade Date editable) ---
with st.form("client_inputs", clear_on_submit=False):
    dt_val = st.date_input("Trade Date", value=dt.date.today(), help="Clients can only edit this value.")
    submitted = st.form_submit_button("Calculate")

if submitted:
    temp = io.BytesIO()
    wb.save(temp)
    temp.seek(0)
    wb_copy = load_workbook(temp, data_only=False, read_only=False)

    ok, err = write_inputs_to_excel(wb_copy, bond_choice, dt_val, cfg)
    if not ok:
        st.warning(f"Trade Date not written: {err}")
    else:
        st.success("Trade Date applied.")

    out_df, out_err = read_output_table(wb_copy, bond_choice, cfg)
    if out_df is not None:
        st.subheader("Results")
        st.dataframe(out_df, use_container_width=True)
    else:
        st.info("No configured output range. Showing preview instead.")
        try:
            pdf = pd.read_excel(EXCEL_PATH, sheet_name=bond_choice, nrows=50)
            st.dataframe(pdf, use_container_width=True)
        except Exception as e:
            st.error(f"Preview failed: {e}")

# Admin config editor
st.divider()
with st.expander("Admin (configure output ranges)"):
    if ADMIN_PASS:
        pwd = st.text_input("Admin password", type="password")
        if pwd != ADMIN_PASS:
            st.warning("Enter correct admin password.")
        else:
            st.success("Admin unlocked.")
            st.code(yaml.safe_dump(cfg, sort_keys=False), language="yaml")
            for s in sheet_names:
                st.markdown(f"#### {s}")
                s_cfg = cfg["sheets"].get(s, {})
                out_rng = st.text_input(f"{s} – Output range (e.g., D8:J20)", value=s_cfg.get("output_range", ""))
                if st.button(f"Save {s}"):
                    cfg["sheets"].setdefault(s, {})
                    if "input_cells" not in cfg["sheets"][s]:
                        cfg["sheets"][s]["input_cells"] = {}
                    cfg["sheets"][s]["output_range"] = out_rng.strip()
                    save_config(cfg)
                    st.success(f"Saved mapping for {s}.")
    else:
        st.info("Set ADMIN_PASS env var to unlock admin editor.")
