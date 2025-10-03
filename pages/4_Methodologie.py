# pages/3_Methodologie.py
import streamlit as st
import plotly.express as px
from utils.scoring import get_weights

# Charger les pondérations
weights = get_weights()

# --- Intro : Origine des données ---
st.header("Origine des données")

st.markdown("""
Les données exploitées dans ce tableau de bord proviennent des **documents PDF**
transmis par les établissements du réseau.
Ces documents ont été analysés automatiquement à l’aide d’une intelligence artificielle,
afin d’en extraire les informations clés (résultats scolaires, projets, infrastructures, etc.).

Toutes ces informations ont ensuite été rassemblées et harmonisées dans un **fichier unique**
(au format tableau), qui sert de base au calcul des scores.

C’est à partir de ce fichier structuré que sont appliquées les étapes suivantes :
- normalisation et transformation des indicateurs,
- calcul des scores par dimension,
- pondération et calcul du score global avec ajustement dynamique en cas de données manquantes.
""")

# --- Méthodologie ---
st.header("Méthodologie de calcul des scores")

st.markdown("""
Cette page décrit la logique appliquée pour construire les scores affichés dans le tableau de bord.
""")

# --- Section 1 : Dimensions ---
st.subheader("1. Dimensions évaluées")

st.markdown("""
Les établissements sont évalués sur **6 dimensions**, chacune ramenée sur 100 :

| Dimensions                               | Indicateurs principaux                                                                 |
|------------------------------------------|----------------------------------------------------------------------------------------|
| **Résultats aux examens (30%)**          | - Taux de réussite au DNB (2024) <br> - Taux de réussite au Bac (2024) |
| **Gouvernance & sécurité (20%)**         | - Statut du projet d’établissement <br> - Fonctionnement des instances représentatives <br> - PPMS (plan particulier de mise en sûreté) |
| **Stratégie & partenariats (15%)**       | - Nombre d’axes stratégiques du projet <br> - Existence de partenariats <br> - Orientation post-bac |
| **Climat & inclusion (15%)**             | - Présence de dispositifs inclusifs (oui / en construction / non) |
| **Ouverture linguistique & culturelle (10%)** | - Nombre de langues vivantes enseignées (0–5 ramenées sur 0–100) <br> - Certifications académiques (DELF, DELE, Cambridge, etc.) |
| **Ressources & numérique (10%)**         | - Infrastructures (niveau de modernité et spécialisation) <br> - Ressources humaines (structuration, stabilité) <br> - Certifications numériques |
""", unsafe_allow_html=True)

# --- Section 2 : Règles ---
st.subheader("2. Règles de transformation")
st.markdown("""
- **Pourcentages** : valeurs ramenées entre 0 et 100 (si déjà en %).
- **Présence/absence** : 80 si renseigné, 40 sinon.
- **Statuts** : valeurs traduites selon une grille (ex. *à jour* = 90, *en construction* = 60, *inexistant* = 30).
- **Listes (axes, certifications, etc.)** : base de 40, +12 points par élément identifié, plafonné à 100.
- **Certifications linguistiques/numériques** : 40 si aucune, 60 si limité (≤2), 90 si nombreuses (>2).
- **Valeurs manquantes** : ignorées dans le calcul de la moyenne de dimension.

Le score global est recalculé dynamiquement : si une dimension manque, ses poids sont redistribués proportionnellement sur les autres.
""")

# --- Section 3 : Pondération ---
st.subheader("3. Pondération du score global")

labels = [
    "Résultats aux examens",
    "Gouvernance & sécurité",
    "Stratégie & partenariats",
    "Climat & inclusion",
    "Ouverture linguistique & culturelle",
    "Ressources & numérique",
]
values = [
    weights["resultats_aux_examens"],
    weights["gouvernance_securite"],
    weights["strategie_partenariats"],
    weights["climat_inclusion"],
    weights["ouverture_linguistique"],
    weights["ressources_numerique"],
]

# Tableau des pondérations
st.table({"Dimension": labels, "Poids": [f"{v:.2f}" for v in values]})

# Diagramme circulaire
fig = px.pie(
    names=labels,
    values=values,
    title="Répartition des pondérations",
    color=labels,
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig.update_traces(
    textinfo="label+percent",
    textposition="outside",
    insidetextorientation="radial",
    pull=[0.05] * len(labels),
)

st.plotly_chart(fig, use_container_width=True)
