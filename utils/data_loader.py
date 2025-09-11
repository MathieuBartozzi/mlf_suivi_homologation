from __future__ import annotations
import pandas as pd
import streamlit as st


CSV_EXPORT = "https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    sheet_id = st.secrets["load_csv"]["sheet_id"]
    gid = st.secrets["load_csv"]["gid"]

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


# Récupérer ID Drive depuis secrets
FILE_ID = st.secrets["ocr_index"]["drive_file_id"]
URL = f"https://drive.google.com/uc?id={FILE_ID}&export=download"

@st.cache_data(show_spinner=False)
def load_index():
    try:
        df_index=pd.read_parquet(URL)
        return df_index
    except Exception as e:
        st.error(f"Impossible de charger l’index OCR depuis Drive : {e}")
        st.stop()
