

from __future__ import annotations
import streamlit as st
from utils.data_loader import load_data
from utils.scoring import compute_scores

st.set_page_config(page_title="MLF – Dashboard",page_icon=":material/dashboard:", layout="wide")
st.title("MLF – Tableau de bord")


with st.spinner("Chargement des données…"):
    df_raw = load_data()
    df = compute_scores(df_raw)

st.session_state['df'] = df


# # --- Définir les pages ---
# overview_page = st.Page(
#     "pages/1_Overview.py",
#     title="Vue réseau",
#     icon=":material/globe:"
# )

# school_page = st.Page(
#     "pages/2_Etablissement.py",
#     title="Vue établissement",
#     icon=":material/school:"
# )

# methodology_page = st.Page(
#     "pages/3_Methodologie.py",
#     title="Méthode & Analyse",
#     icon=":material/lightbulb_2:"
# )
# pg = st.navigation([overview_page, school_page, methodology_page],position="top")


# --- Navigation ---
pages = [
         st.Page("pages/1_Overview.py",title="RÉSEAU",icon=":material/globe:"),
         st.Page("pages/2_Etablissement.py",title="ÉTABLISSEMENT",icon=":material/school:"),
         st.Page("pages/3_Methodologie.py",title="MÉTHODE",icon=":material/lightbulb_2:")]

pg = st.navigation(pages,position="top")

# --- Exécuter la page active ---
pg.run()
