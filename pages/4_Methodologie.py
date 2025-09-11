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
- normalisation des indicateurs,
- calcul des scores par thématique,
- pondération et calcul du score global.
""")

# --- Méthodologie ---
st.header("Méthodologie de calcul des scores")

st.markdown("""
Cette page décrit la logique appliquée pour construire les scores affichés dans le tableau de bord.
""")

# --- Section 1 : Dimensions ---
st.subheader("1. Dimensions évaluées")
st.markdown("""
Les établissements sont évalués sur **5 dimensions**, chacune ramenée sur 100 :

1. **Qualité de l’enseignement**
   - Taux de réussite au DNB (2024)
   - Taux de réussite au Bac (2024)

2. **Sécurité & bien-être**
   - Statut du PPMS (plan particulier de mise en sûreté)
   - Fonctionnement des instances représentatives

3. **Projets & partenariats**
   - Statut du projet d’établissement
   - Nombre d’axes renseignés dans le projet
   - Existence de partenariats

4. **Inclusion & climat scolaire**
   - Dispositifs d’inclusion renseignés
   - Nombre de langues vivantes enseignées (0–5 ramenées sur 0–100)
   - Certifications spécifiques

5. **Numérique & données**
   - Infrastructures mentionnées (wifi, CDI, gymnase, etc.)
   - Certifications associées
""")

# --- Section 2 : Règles ---
st.subheader("2. Règles de transformation")
st.markdown("""
- **Pourcentages** : convertis sur 0–100 (si la donnée est entre 0 et 1, elle est multipliée par 100).
- **Présence** : 80 si renseigné, 40 sinon.
- **Statut** : 90 si *à jour/ok*, 60 si *en cours/partiel*, 30 si *non conforme/absent*.
- **Listes** : base de 40, +12 points par élément renseigné, plafonné à 100.
- **Mots-clés** : base de 40, +12 points par mot-clé trouvé, plafonné à 100.

Toutes les moyennes sont calculées en ignorant les valeurs manquantes.
""")

# --- Section 3 : Pondération ---
st.subheader("3. Pondération du score global")

labels = [
    "Qualité de l’enseignement",
    "Sécurité & bien-être",
    "Projets & partenariats",
    "Inclusion & climat scolaire",
    "Numérique & données",
]
values = [
    weights["qualite_enseignement"],
    weights["securite_bien_etre"],
    weights["projets_partenariats"],
    weights["inclusion_climat"],
    weights["numerique_donnees"],
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
