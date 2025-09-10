# pages/1_Overview.py
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.header("Vue d’ensemble du réseau")

df = st.session_state.get('df')
if df is None or df.empty:
    st.warning("Aucune donnée disponible. Ouvrez la page Home")
    st.stop()

# --- Contrôles
METRICS = {
    "Score global": "score_global",
    "Qualité de l’enseignement": "score_qualite_enseignement",
    "Sécurité & bien-être": "score_securite_bien_etre",
    "Projets & partenariats": "score_projets_partenariats",
    "Inclusion & climat scolaire": "score_inclusion_climat",
    "Numérique & données": "score_numerique_donnees",
}



# --- KPIs (6 x st.metric)
col1,col2=st.columns([1,3])

kpis = {
    # "Score global": df["score_global"].mean(),
    "Qualité de l’enseignement": df["score_qualite_enseignement"].mean(),
    "Sécurité & bien-être": df["score_securite_bien_etre"].mean(),
    "Projets & partenariats": df["score_projets_partenariats"].mean(),
    "Inclusion & climat scolaire": df["score_inclusion_climat"].mean(),
    "Numérique & données": df["score_numerique_donnees"].mean(),
}

with col1 :
    with st.container(border=True):
        mean_score = df["score_global"].mean()
        st.metric("Score global", f"{mean_score:.1f}/100")
    with st.container(border=True):
        kpis_df = (
            pd.DataFrame.from_dict(kpis, orient="index", columns=["valeur"])
            .reset_index()
            .rename(columns={"index": "indicateur"})
            .sort_values("valeur", ascending=True)
        )


        fig = px.bar(
        kpis_df,
        x="valeur",
        y="indicateur",
        orientation="h",
        text="valeur",
        height=420
    )

    # Améliorer le rendu
        fig.update_traces(
            texttemplate="%{text:.1f}",
            textposition="inside"
        )

        fig.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis_title=None,
            yaxis_title=None,
            coloraxis_showscale=False   # cacher la légende du dégradé si tu veux
        )

        st.plotly_chart(fig, use_container_width=True)



with col2 :
    metric_label = st.pills(
        "Choix de l’indicateur",
        options=list(METRICS.keys()),
        selection_mode="single",
        default="Score global",
    )
    metric_col = METRICS[metric_label]

    lat_col, lon_col = "latitude", "longitude"
    name_col = "etablissement"
    has_geo = all(c in df.columns for c in (lat_col, lon_col, name_col))
    map_df = df.dropna(subset=[lat_col, lon_col])
    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="etablissement",
        color=metric_col,
        color_continuous_scale="Viridis",
        zoom=1,
        height=500,
        custom_data=[df["score_global"]],  # <-- on injecte le score global
    )

    # Customiser le hover (nom + score global)
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>Score global = %{customdata[0]:.1f}<extra></extra>"
    )

    fig.update_layout(mapbox_style="carto-positron", margin=dict(l=0, r=0, t=0, b=0))


        # Fixer la taille des points et l'opacité
    fig.update_traces(marker=dict(size=15, opacity=0.7))

        # Mise en page et affichage
    fig.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0),coloraxis_colorbar=dict(title="Moyenne"))
    st.plotly_chart(fig, use_container_width=True)

st.divider()



st.subheader("Classements")


def ranking_table(d: pd.DataFrame, metric: str, top: bool = True, n: int = 10) -> pd.DataFrame:
    cols = ["etablissement", "pays", "ville", metric]
    if metric != "score_global":
        cols.append("score_global")

    dd = d[cols].copy()
    dd = dd.dropna(subset=[metric])
    dd = dd.sort_values(by=metric, ascending=not top).head(n)

    # Renommer la colonne sélectionnée
    dd = dd.rename(columns={metric: f"{metric} (sélection)"})
    return dd.reset_index(drop=True)


ltab, rtab = st.tabs(["Top 3", "Bottom 3"])
with ltab:
    top_df = ranking_table(df, metric_col, top=True, n=3)
    st.dataframe(top_df, use_container_width=True)
with rtab:
    bottom_df = ranking_table(df, metric_col, top=False, n=3)
    st.dataframe(bottom_df, use_container_width=True)

st.divider()

# # --- Table brute (expander)
# with st.expander("Table brute (toutes colonnes)"):
#     st.dataframe(df, use_container_width=True)
