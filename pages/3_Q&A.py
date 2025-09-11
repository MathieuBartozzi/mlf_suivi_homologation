

import numpy as np
import streamlit as st
from openai import OpenAI
from utils.data_loader import load_index

# ---- Config OpenAI ----
client = OpenAI(api_key=st.secrets["KEY"]["OPENAI_API_KEY"])

# ---- Charger index vectoriel ----
if "df_index" not in st.session_state:
    st.session_state["df_index"] = load_index()

df_index = st.session_state["df_index"]

# ---- Liste des établissements disponibles ----
ETABS = sorted(df_index["doc"].unique())

# ---- Similarité cosinus ----
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# ---- Détection d’établissement dans la question ----
def detect_etab(query: str) -> str | None:
    for etab in ETABS:
        if etab.lower().replace("_", " ") in query.lower():
            return etab
    return None

# ---- Recherche ----
def search(query, etab=None, top_k=5, model="text-embedding-3-small"):
    resp = client.embeddings.create(model=model, input=query)
    query_emb = np.array(resp.data[0].embedding)

    sub_df = df_index if etab is None else df_index[df_index["doc"] == etab]

    sims = []
    for _, row in sub_df.iterrows():
        if row["embedding"] is None:
            continue
        emb = np.array(row["embedding"])
        sims.append((cosine_similarity(query_emb, emb), row["doc"], row["page"], row["text"]))

    return sorted(sims, key=lambda x: x[0], reverse=True)[:top_k]

# ---- Génération réponse (non streaming) ----
def answer_question(query, top_k=5):
    etab = detect_etab(query)
    results = search(query, etab=etab, top_k=top_k)

    context = "\n\n".join([f"[{doc}, p.{page}] {text[:800]}..." for _, doc, page, text in results])

    if etab:
        system_prompt = f"""
        Tu es un assistant expert en analyse et synthèse de rapports d’homologation et de suivi
        d’établissements français à l’étranger.

        Contexte : tu aides l’équipe de pilotage de la Mission Laïque Française / OSUI (tête de réseau)
        à exploiter ces documents. Réponds UNIQUEMENT pour l’établissement : {etab}.

        Règles de réponse :
        - Appuie-toi uniquement sur les extraits fournis (ne jamais inventer).
        - Structure systématiquement la réponse avec des titres clairs.
        - Mets les éléments en liste à puces pour la lisibilité.
        - Intègre toujours les références de pages quand elles sont disponibles.
        - Organise la réponse autour des rubriques suivantes si possible :
            * Gouvernance et contexte
            * Atouts et points forts
            * Points de vigilance / critiques
            * Recommandations et axes de travail prioritaires
            * Enjeux pour le pilotage réseau (MLF/OSUI)
        - Si la question implique une comparaison avec d’autres établissements, présente une
        analyse comparative structurée.
        - Termine par une courte synthèse stratégique orientée “tête de réseau”.
        """
    else:
        system_prompt = """
        Tu es un assistant expert en analyse et synthèse de rapports d’homologation et de suivi
        d’établissements français à l’étranger.

        Contexte : tu aides l’équipe de pilotage de la Mission Laïque Française / OSUI (tête de réseau)
        à exploiter ces documents. Réponds en t’appuyant uniquement sur les extraits fournis.

        Règles de réponse :
        - Appuie-toi uniquement sur les extraits fournis (ne jamais inventer).
        - Structure systématiquement la réponse avec des titres clairs.
        - Mets les éléments en liste à puces pour la lisibilité.
        - Intègre toujours les références de pages quand elles sont disponibles.
        - Organise la réponse autour des rubriques suivantes si possible :
            * Gouvernance et contexte
            * Atouts et points forts
            * Points de vigilance / critiques
            * Recommandations et axes de travail prioritaires
            * Enjeux pour le pilotage réseau (MLF/OSUI)
        - Si la question implique une comparaison avec plusieurs établissements, présente une
        analyse comparative structurée.
        - Termine par une courte synthèse stratégique orientée “tête de réseau”.
        """


    user_prompt = f"Question : {query}\n\nExtraits :\n{context}"

    response = client.chat.completions.create(
        model="gpt-5",
        temperature=1,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content

# ---- UI ----
st.header("Votre espace de questions")

st.warning(
    "Cet outil vous permet de poser vos questions sur les données disponibles. "
    "Les réponses sont générées automatiquement et peuvent être approximatives. "
    "Il est proposé en version bêta : à utiliser comme une aide à l’exploration, "
    "et non comme une source unique de vérité."
)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Afficher l’historique
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])   # ✅ Markdown rendu correctement

# Input utilisateur
if query := st.chat_input("Pose ta question sur les rapports d’homologation..."):
    # Sauvegarde et affichage de la question utilisateur
    st.session_state["messages"].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Génération et affichage de la réponse
    answer = answer_question(query)
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)   # ✅ Markdown bien rendu
