
# utils/scoring.py
from __future__ import annotations
import pandas as pd
import numpy as np
import streamlit as st
import ast
import re

# Utilitaires

# Pondérations par défaut (fixes, versionnées avec le code)
DEFAULT_WEIGHTS = {
    "qualite_enseignement": 0.25,
    "securite_bien_etre": 0.20,
    "projets_partenariats": 0.20,
    "inclusion_climat": 0.20,
    "numerique_donnees": 0.15,
}


def _to_percent(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors='coerce')
    # si probable fraction (0–1), on convertit en %
    if x.dropna().between(0, 1).mean() > 0.8:
        x = x * 100
    return x.clip(0, 100)


def _presence_score(series: pd.Series) -> pd.Series:
    # 80 si non vide, 40 sinon
    def f(val):
        if val is None:
            return np.nan
        s = str(val).strip().lower()
        if s in ("", "nan", "none", "n/a", "na"):
            return 40.0
        return 80.0
    return series.map(f)


def _status_score(series: pd.Series) -> pd.Series:
    # mapping simple basé sur mots-clés usuels
    def f(val):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return np.nan
        s = str(val).lower()
        if any(k in s for k in ["à jour", "a jour", "ok", "actif", "valide", "conforme"]):
            return 90.0
        if any(k in s for k in ["en cours", "partiel", "partiellement", "à mettre à jour", "a mettre a jour"]):
            return 60.0
        if any(k in s for k in ["non", "absent", "inactif", "non conforme"]):
            return 30.0
        return 70.0
    return series.map(f)


def _len_list_score(series: pd.Series, base: float = 40.0, step: float = 12.0, cap: float = 100.0) -> pd.Series:
    def f(val):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return np.nan
        s = str(val).strip()
        try:
            lst = ast.literal_eval(s) if (s.startswith("[") and s.endswith("]")) else []
            L = len(lst)
            return float(min(cap, base + L * step))
        except Exception:
            return np.nan
    return series.map(f)


def _keyword_count_score(series: pd.Series, keywords=None) -> pd.Series:
    if keywords is None:
        keywords = ["wifi", "laboratoire", "labo", "cdi", "gymnase", "terrain", "tablettes", "ordinateurs"]
    regex = re.compile("|".join(map(re.escape, keywords)), re.IGNORECASE)
    def f(val):
        if not isinstance(val, str):
            return np.nan
        count = len(regex.findall(val))
        return float(min(100, 40 + count * 12))
    return series.map(f)


def _mean_ignore_nan(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    sub = df[cols].copy()
    return sub.apply(pd.to_numeric, errors='coerce').mean(axis=1)


# Calcul des 5 scores + global

def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Proxies par thématique (ajustables si besoin)
    # 1) Qualité de l’enseignement
    q_dnb = _to_percent(df.get('dnb_2024'))
    q_bac = _to_percent(df.get('bac_2024'))
    score_qualite = _mean_ignore_nan(pd.concat({'dnb': q_dnb, 'bac': q_bac}, axis=1), ['dnb', 'bac'])

    # 2) Sécurité & bien-être
    s_ppms = _status_score(df.get('ppms_status'))
    s_instances = _status_score(df.get('instances_status'))
    score_securite = _mean_ignore_nan(pd.concat({'ppms': s_ppms, 'inst': s_instances}, axis=1), ['ppms', 'inst'])

    # 3) Projets & partenariats
    p_proj_stat = _status_score(df.get('projet_etablissement_status'))
    p_proj_axes = _len_list_score(df.get('projet_etablissement_axes'))
    p_part = _presence_score(df.get('partenariats'))
    score_projets = _mean_ignore_nan(pd.concat({'stat': p_proj_stat, 'axes': p_proj_axes, 'part': p_part}, axis=1), ['stat', 'axes', 'part'])

    # 4) Inclusion & climat scolaire
    i_inclusion = _presence_score(df.get('inclusion_dispositif'))
    i_lve = _to_percent(df.get('nb_lve'))  # si nb_lve est un compte, on le ramène grossièrement: <=5 → 0–100
    if 'nb_lve' in df.columns:
        # si nb_lve ressemble à un petit entier (0–8), on scale simple
        x = pd.to_numeric(df['nb_lve'], errors='coerce')
        i_lve = (x.fillna(0).clip(0, 5) / 5.0) * 100.0
    i_certif = _presence_score(df.get('certifications'))
    score_inclusion = _mean_ignore_nan(pd.concat({'inc': i_inclusion, 'lve': i_lve, 'cert': i_certif}, axis=1), ['inc', 'lve', 'cert'])

    # 5) Numérique & données
    n_infra = _keyword_count_score(df.get('infrastructures'))
    n_certif = _presence_score(df.get('certifications'))
    score_numerique = _mean_ignore_nan(pd.concat({'infra': n_infra, 'cert': n_certif}, axis=1), ['infra', 'cert'])

    # Assemblage + normalisation douce 0–100
    for name, s in [
        ('score_qualite_enseignement', score_qualite),
        ('score_securite_bien_etre', score_securite),
        ('score_projets_partenariats', score_projets),
        ('score_inclusion_climat', score_inclusion),
        ('score_numerique_donnees', score_numerique),
    ]:
        df[name] = s.clip(lower=0, upper=100)

    # Score global pondéré
    weights = DEFAULT_WEIGHTS  # ← plus de st.secrets

    total = sum(weights.values()) or 1.0
    wq, ws, wp, wi, wn = [weights[k] / total for k in DEFAULT_WEIGHTS]

    df["score_global"] = (
        df["score_qualite_enseignement"] * wq +
        df["score_securite_bien_etre"]    * ws +
        df["score_projets_partenariats"]  * wp +
        df["score_inclusion_climat"]      * wi +
        df["score_numerique_donnees"]     * wn
    ).round(1)

    return df

def get_weights() -> dict[str, float]:
    total = sum(DEFAULT_WEIGHTS.values()) or 1.0
    return {k: v/total for k, v in DEFAULT_WEIGHTS.items()}

