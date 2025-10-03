import streamlit as st
import plotly.express as px

# Bouton de génération du rapport
if st.button("⚙️ Générer le rapport",type='primary'):

    with st.spinner("🚧 Votre rapport est en cours de création. Merci de patienter un instant ⏳..."):

        # Filtrer les données pour l'établissement sélectionné
        df_etablissement = df[df["Nom d'établissement"] == nom_etablissement_selectionne]

        # Vérifier s'il y a des données pour cet établissement
        if df_etablissement.empty:
            st.error("Aucune donnée disponible pour cet établissement.")
        else:

            # Récupérer les informations de l'établissement
            ville, pays = df_etablissement.iloc[0][["Ville", "Pays"]]
            niveaux = ", ".join(df_etablissement["Niveau scolaire"].unique())

            # Titre du rapport
            titre_rapport = f"Rapport d'analyse pour l'établissement {selected_etablissement} ({ville}, {pays})\nDonnées des évaluations nationales 2024"
            avertissement ="Ce rapport a été généré automatiquement par une intelligence artificielle et doit être interprété avec prudence. Il s’agit d’une analyse basée sur les données fournies, et toute décision doit être complétée par une réflexion pédagogique et des échanges avec les équipes enseignantes."

            # Regrouper les scores moyens par **niveau scolaire et compétence**
            resultats = df_etablissement.groupby(["Niveau scolaire", "Compétence évaluée"])["Valeur"].mean().reset_index()

            # Convertir les résultats en format lisible
            resultats_str = "\n".join([
                f"- {row['Niveau scolaire']} | {row['Compétence évaluée']} : {row['Valeur']:.1f}%"
                for _, row in resultats.iterrows()
            ])

            # Construction du prompt OpenAI
            prompt = f"""

            Tu es un expert en éducation et en analyse des résultats scolaires.
            Ton objectif est d’aider un chef d’établissement à interpréter les performances de ses élèves et à identifier des pistes d’amélioration et de formation.
            Tu dois fournir une analyse claire et structurée en adoptant un ton professionnel et neutre. Les éléments factuels sur les données chiffrées doivent etre présentés comme tel, les propositions de pistes d'actions ou de refelxion sont à mettre au conditionnel pour renforcer ton rôle de conseiller.
            Emploi un language extrement clair et professionnel, tout en etant bienveillant.

            # {titre_rapport}

            ### **Contexte**
            L’établissement **{selected_etablissement}**, situé à **{ville}, {pays}**, a récemment obtenu des résultats aux évaluations nationales pour les niveaux suivants : **{niveaux}**.

            **Scores moyens par niveau et par compétence :**
            {resultats_str}

            Juste apres le titre, il faut faire apparaitre obligatoirement le message {avertissement} en gras et encadré.
            """

            if contexte_local:
                prompt += f"\n**Informations spécifiques fournies par l'établissement :**\n{contexte_local}\n"

            # Ajouter le contenu extrait du PDF si disponible
            if pdf_text:
                prompt += f"\n**Informations complémentaires extraites du document joint :**\n{pdf_text[:1500]}..."  # Limite à 1500 caractères pour éviter un prompt trop long

            prompt += """
            ### **Analyse des résultats**
            1. **Identification des tendances marquantes**
            - Décris les principales forces et points à renforcer observés dans les résultats.
            - Mets en évidence des évolutions inhabituelles (ex. chute ou progression marquée d’un niveau à l’autre).
            - Si possible, compare avec des références extérieures (moyenne du réseau ou nationale).

            2 **Interprétation pédagogique**
            - Quels facteurs pourraient expliquer ces résultats ?
            - Existe-t-il des corrélations entre certaines compétences ?
            - Ces résultats pourraient-ils être liés à des approches pédagogiques spécifiques ?

            3. **Pistes d’amélioration possible**
            - Quelles stratégies pourraient être mises en place pour améliorer les compétences identifiées comme faibles ?
            - Quels ajustements pédagogiques pourraient être envisagés ?
            - Des interventions ciblées sur certaines compétences pourraient-elles être bénéfiques ?

            4. **Besoins de formation pour les enseignants**
            - Quelles formations pourraient être recommandées sur la base des tendances observées ?
            - Quels axes de formation seraient les plus pertinents pour renforcer les pratiques pédagogiques ?
            - Comment ces formations pourraient-elles être intégrées dans une stratégie d’amélioration continue ?
            """

            # Sélection du modèle OpenAI
            model = "gpt-4o-mini"

            # Appel API OpenAI
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])  # Assure-toi d'avoir la clé API dans secrets.toml
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )

            # Récupération de la réponse
            rapport = response.choices[0].message.content

            st.write("C'est prêt 😊 !")
            with st.expander('**Consulter le rapport**', icon= "📄"):
                st.write(rapport)
