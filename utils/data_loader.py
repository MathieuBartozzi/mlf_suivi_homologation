# utils/data_loader.py
from __future__ import annotations
import pandas as pd
import streamlit as st


CSV_EXPORT = "https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


@st.cache_data()
def load_data() -> pd.DataFrame:
    sheet_id = st.secrets["sheet_id"]
    gid = st.secrets["gid"]

    if not sheet_id:
        st.error("sheet_id manquant dans .streamlit/secrets.toml")
        st.stop()
    url = CSV_EXPORT.format(sheet_id=sheet_id, gid=gid)
    df = pd.read_csv(url)
    # Normalisation colonnes
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("/", "_")


    # Normalisation des noms de colonnes
    df.columns = (
    df.columns
    .str.strip().str.lower()
    .str.replace(" ", "_", regex=False)
    .str.replace("/", "_", regex=False)
    )

    return df
