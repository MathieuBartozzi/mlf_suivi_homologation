

from __future__ import annotations
import streamlit as st
from utils.data_loader import load_data
from utils.scoring import compute_scores
from utils.data_loader import load_index
from utils.authenticate import authenticate, logout



st.set_page_config(page_title="MLF – Dashboard",page_icon=":material/dashboard:", layout="wide")

user = authenticate()

if st.session_state.get("show_welcome", False):
    st.success(f"Bienvenue, {user} ! 🎉")
    st.session_state["show_welcome"] = False

# Étape 1
with st.spinner("Chargement des données…"):
        df = load_data()
        df = compute_scores(df)
        df_index = load_index()



st.session_state['df'] = df
st.session_state['df_index'] = df_index



# --- Navigation ---
pages = [
         st.Page("pages/1_Overview.py",title="RÉSEAU",icon=":material/globe:"),
         st.Page("pages/2_Etablissement.py",title="ÉTABLISSEMENT",icon=":material/school:"),
         st.Page("pages/3_Q&A.py",title="Q&A",icon=":material/school:"),
         st.Page("pages/4_Methodologie.py",title="MÉTHODE",icon=":material/lightbulb_2:")]

pg = st.navigation(pages,position="top")

# --- Exécuter la page active ---
pg.run()


# Bouton de déconnexion
if st.sidebar.button("Se déconnecter"):
    logout()
