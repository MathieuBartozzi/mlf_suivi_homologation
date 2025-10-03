
import pandas as pd
import numpy as np

# --------------------
# Pondérations par défaut (6 dimensions)
# --------------------
DEFAULT_WEIGHTS = {
    "resultats_aux_examens": 0.30,
    "gouvernance_securite": 0.20,
    "strategie_partenariats": 0.15,
    "climat_inclusion": 0.15,
    "ouverture_linguistique": 0.10,
    "ressources_numerique": 0.10,
}

# --------------------
# Fonctions utilitaires réellement utilisées
# --------------------
def _to_percent(s) -> pd.Series:
    """Convertit en pourcentage (0–100). Données déjà en entiers, donc pas de *100."""
    if s is None:
        return pd.Series([np.nan])
    if not isinstance(s, (pd.Series, pd.DataFrame)):
        s = pd.Series([s])
    x = pd.to_numeric(s, errors="coerce")
    return x.clip(0, 100)


def _presence_score(series: pd.Series) -> pd.Series:
    """Score simple présence/absence : 80 si renseigné, 40 sinon."""
    def f(val):
        if val is None:
            return np.nan
        s = str(val).strip().lower()
        if s in ("", "nan", "none", "n/a", "na", "non précisé"):
            return 40.0
        return 80.0
    return series.map(f)

# --------------------
# Calcul des scores
# --------------------
def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.lower()  # harmoniser les noms de colonnes

    # === 1. Résultats aux examens ===
    q_dnb = _to_percent(df.get("dnb_2024"))
    q_bac = _to_percent(df.get("bac_2024"))
    df["score_resultats_aux_examens"] = pd.concat({"dnb": q_dnb, "bac": q_bac}, axis=1).mean(axis=1)

    # === 2. Gouvernance & sécurité ===
    map_proj = {"à jour": 90, "en construction": 60, "partiel": 60, "inexistant": 30}
    map_ppms = {"validé": 90, "en attente": 60, "pas d'information": 40}
    map_instances = {"complètes": 90}

    df["score_gouvernance_securite"] = pd.concat({
        "proj": df["projet_etablissement_status"].map(map_proj),
        "ppms": df["ppms_status"].map(map_ppms),
        "inst": df["instances_status"].map(map_instances).fillna(70),
    }, axis=1).mean(axis=1)

    # === 3. Stratégie & partenariats ===
    def score_axes(val):
        if pd.isna(val):
            return np.nan
        return min(100, 40 + len(str(val).split(",")) * 12)

    map_orientation = {
        "structuré mais diversifié": 90,
        "structuré vers la france": 80,
        "centré sur le pays hôte": 70,
        "dispositif limité / informel": 40,
        "—": 30,
    }

    df["score_strategie_partenariats"] = pd.concat({
        "axes": df["projet_etablissement_axes"].map(score_axes),
        "part": df["partenariats"].apply(lambda x: 80 if pd.notna(x) and str(x).strip() != "" else 40),
        "orient": df["orientation_post_bac"].str.lower().map(map_orientation),
    }, axis=1).mean(axis=1)

    # === 4. Climat & inclusion ===
    map_inclusion = {"oui": 90, "en construction": 60, "non": 30}
    df["score_climat_inclusion"] = df["inclusion_dispositif"].str.lower().map(map_inclusion)

    # === 5. Ouverture linguistique & culturelle ===
    x = pd.to_numeric(df.get("nb_lve"), errors="coerce")
    lve_score = (x.fillna(0).clip(0, 5) / 5.0) * 100

    def score_certifs(val):
        if not isinstance(val, str) or val.strip().lower() in ["", "non précisé"]:
            return 40
        n = len(val.split(","))
        return 60 if n <= 2 else 90

    certif_score = df["certifications"].map(score_certifs)

    df["score_ouverture_linguistique"] = pd.concat({
        "lve": lve_score,
        "cert": certif_score,
    }, axis=1).mean(axis=1)

    # === 6. Ressources & numérique ===
    map_infra = {
        "limitées": 30,
        "fonctionnelles de base": 60,
        "diversifiées et spécialisées": 80,
        "campus complet et moderne": 100,
    }
    map_rh = {"structuré": 90, "perfectible": 70, "fragilisé": 40, "critique": 20}

    df["score_ressources_numerique"] = pd.concat({
        "infra": df["infrastructures"].str.lower().map(map_infra),
        "rh": df["ressources_humaines"].str.lower().map(map_rh),
        "certnum": df["certifications"].map(score_certifs),
    }, axis=1).mean(axis=1)

    # === Score global avec ajustement dynamique ===
    weights = DEFAULT_WEIGHTS.copy()
    score_to_weight = {
        "score_resultats_aux_examens": "resultats_aux_examens",
        "score_gouvernance_securite": "gouvernance_securite",
        "score_strategie_partenariats": "strategie_partenariats",
        "score_climat_inclusion": "climat_inclusion",
        "score_ouverture_linguistique": "ouverture_linguistique",
        "score_ressources_numerique": "ressources_numerique",
    }

    global_scores, incomplete_flags, missing_texts = [], [], []
    for _, row in df.iterrows():
        vals = {col: row[col] for col in score_to_weight.keys()}
        valid_dims = {k: v for k, v in vals.items() if not pd.isna(v)}
        missing = [k for k, v in vals.items() if pd.isna(v)]

        if not valid_dims:
            global_scores.append(np.nan)
            incomplete_flags.append(True)
            missing_texts.append("Toutes les dimensions manquent")
            continue

        sub_weights = {k: weights[score_to_weight[k]] for k in valid_dims}
        total_w = sum(sub_weights.values())
        norm_weights = {k: w / total_w for k, w in sub_weights.items()}

        gscore = sum(valid_dims[k] * norm_weights[k] for k in valid_dims)
        global_scores.append(round(gscore, 1))
        incomplete_flags.append(len(missing) > 0)
        missing_texts.append("Score calculé sans : " + ", ".join(missing) if missing else "Complet")

    df["score_global"] = global_scores
    df["incomplete_score"] = incomplete_flags
    df["missing_dimensions"] = missing_texts

        # === Arrondir toutes les colonnes de score ===
    score_cols = [
        "score_resultats_aux_examens",
        "score_gouvernance_securite",
        "score_strategie_partenariats",
        "score_climat_inclusion",
        "score_ouverture_linguistique",
        "score_ressources_numerique",
        "score_global",
    ]
    df[score_cols] = df[score_cols].round(1)

    return df


def get_weights() -> dict[str, float]:
    total = sum(DEFAULT_WEIGHTS.values()) or 1.0
    return {k: v / total for k, v in DEFAULT_WEIGHTS.items()}
