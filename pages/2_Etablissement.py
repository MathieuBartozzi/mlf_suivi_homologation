# pages/2\_Etablissement.py (fiche individuelle)

# pages/2_Etablissement.py
from __future__ import annotations
import ast
import math
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.header("Fiche établissement")

df: pd.DataFrame | None = st.session_state.get("df")
if df is None or df.empty:
    st.warning("Aucune donnée disponible.")
    st.stop()

# ---- Utilitaires locaux -----------------------------------------------------
THEMES = [
    ("Qualité de l’enseignement", "score_qualite_enseignement"),
    ("Sécurité & bien-être", "score_securite_bien_etre"),
    ("Projets & partenariats", "score_projets_partenariats"),
    ("Inclusion & climat scolaire", "score_inclusion_climat"),
    ("Numérique & données", "score_numerique_donnees"),
]

# Colonnes multi-valeurs affichées comme texte avec virgules
TEXT_LIST_COLS = ["projet_etablissement_axes", "partenariats"]

# Colonnes multi-valeurs affichées comme puces (une par ligne)
BULLET_LIST_COLS = ["points_forts", "points_faibles", "recommandations"]


INFO_BLOCKS = [
    ("Profil & effectifs", ["nb_niveaux", "niveau_max", "effectifs_total"]),
    ("Projet & instances", ["projet_etablissement_status", "projet_etablissement_axes", "instances_status"]),
    ("Évaluations & résultats", ["evaluations_nationales", "dnb_2024", "bac_2024"]),
    ("Inclusion & langues", ["inclusion_dispositif", "nb_lve", "certifications"]),
    ("Infrastructures & sécurité", ["infrastructures", "ppms_status"]),
    ("Ressources humaines", ["ressources_humaines", "nb_personnels"]),
    ("Partenariats & orientation", ["partenariats", "orientation_post_bac"]),
]


# def parse_list_cell(val) -> list[str]:
#     if isinstance(val, list):
#         return [str(x) for x in val]
#     if val is None or (isinstance(val, float) and math.isnan(val)):
#         return []
#     s = str(val).strip()
#     if not s:
#         return []
#     try:
#         if s.startswith("[") and s.endswith("]"):
#             out = ast.literal_eval(s)
#             if isinstance(out, list):
#                 return [str(x) for x in out]
#     except Exception:
#         pass
#     # fallback: retourner la chaîne unique comme item
#     return [s]

def format_cell(val, col):
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "—"
    s = str(val).strip()
    if not s:
        return "—"

    if col in TEXT_LIST_COLS:
        # On garde les virgules comme séparateur
        return s

    if col in BULLET_LIST_COLS:
        items = [x.strip() for x in s.split(",") if x.strip()]
        return "\n".join([f"• {it}" for it in items]) if items else "—"

    return s



def score_mean(series: pd.Series) -> float:
    s = pd.to_numeric(series, errors="coerce")
    return float(s.mean()) if s.notna().any() else float("nan")

# ---- Sélecteur d'établissement ---------------------------------------------
name_col = "etablissement"
if name_col not in df.columns:
    st.error("Colonne 'etablissement' introuvable dans la source.")
    st.stop()

# Construire un label enrichi : "etablissement – ville (pays)"
choices = []
labels = {}
for _, r in df.iterrows():
    etab = str(r.get("etablissement", "—"))
    ville = str(r.get("ville", "—"))
    pays = str(r.get("pays", "—"))
    label = f"{etab} – {ville} ({pays})"
    choices.append(label)
    labels[label] = etab  # mapping vers le vrai nom d'établissement

# Sélecteur dans la sidebar
selected_label = st.sidebar.selectbox("Choisir un établissement", sorted(choices))

# Récupérer la ligne correspondante
selected_etab = labels[selected_label]
row = df[df[name_col] == selected_etab].iloc[0]

# ---- En-tête: KPI + infos ---------------------------------------------------
st.subheader(selected_label)
left, right = st.columns([1, 1])
with left:
    # Mapping des noms techniques -> labels lisibles
    INDICATOR_LABELS = {
        "nb_niveaux": "Nombre de niveaux",
        "niveau_max": "Niveau maximum",
        "effectifs_total": "Effectifs total",
        "projet_etablissement_status": "Projet établissement (statut)",
        "projet_etablissement_axes": "Axes du projet",
        "instances_status": "Instances (statut)",
        "evaluations_nationales": "Évaluations nationales",
        "dnb_2024": "Résultats DNB 2024",
        "bac_2024": "Résultats BAC 2024",
        "inclusion_dispositif": "Dispositif inclusion",
        "nb_lve": "Nombre de LVE",
        "certifications": "Certifications",
        "infrastructures": "Infrastructures",
        "ppms_status": "PPMS (sécurité)",
        "ressources_humaines": "Ressources humaines",
        "nb_personnels": "Nombre de personnels",
        "partenariats": "Partenariats",
        "orientation_post_bac": "Orientation post-bac",
    }

    rows = []
    for title, cols in INFO_BLOCKS:
        for c in cols:
            raw = row.get(c, None)
            value = format_cell(raw, c)
            label = INDICATOR_LABELS.get(c, c.replace("_", " ").capitalize())
            rows.append({"Indicateur": label, "Valeur": value})

    DF_details = pd.DataFrame(rows)

    # Respect des retours à la ligne pour les bullets
    DF_details = DF_details.style.set_properties(**{'white-space': 'pre-wrap'})

    st.dataframe(DF_details, use_container_width=True)


with right:
    cats = [t[0] for t in THEMES]
    etab_vals = [row.get(col, None) for _, col in THEMES]
    mean_vals = [score_mean(df[col]) if col in df.columns else float("nan") for _, col in THEMES]


    df_radar = pd.DataFrame({
    "theta": cats * 2,
    "r": etab_vals + mean_vals,
    "Source": ["Établissement"] * len(cats) + ["Réseau"] * len(cats),
    })


    fig = px.line_polar(
    df_radar,
    r="r",
    theta="theta",
    color="Source",
    line_close=True,
    )
    fig.update_traces(fill="toself")
    fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    # title="📊 Profil des scores",
    height=420,
    template="plotly_white",
    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
    margin=dict(l=0, r=0, t=40, b=0),
    )
    # Remplissage uniquement pour l'établissement
    fig.update_traces(fill="toself", selector=dict(name="Établissement"))

    # La moyenne réseau → ligne simple (pas de remplissage, couleur spécifique)
    fig.update_traces(
        fill=None,
        line=dict(color=px.colors.qualitative.G10[9], dash="dash"),
        selector=dict(name="Réseau"),
    )
        # Layout
    fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=350,
            template="plotly_white",
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
            margin=dict(l=0, r=0, t=40, b=0),
        )
    st.plotly_chart(fig)


# Points forts
pf_items = [x.strip() for x in str(row.get("points_forts", "")).split(",") if x.strip()]
df_pf = pd.DataFrame({"⊕ Points forts": pf_items if pf_items else ["—"]})
st.dataframe(df_pf, use_container_width=True, height=200)

# Points faibles
pfb_items = [x.strip() for x in str(row.get("points_faibles", "")).split(",") if x.strip()]
df_pfb = pd.DataFrame({"⊖ Points faibles": pfb_items if pfb_items else ["—"]})
st.dataframe(df_pfb, use_container_width=True, height=200)

# Recommandations
reco_items = [x.strip() for x in str(row.get("recommandations", "")).split(",") if x.strip()]
df_reco = pd.DataFrame({"💡 Recommandations": reco_items if reco_items else ["—"]})
st.dataframe(df_reco, use_container_width=True, height=200)
