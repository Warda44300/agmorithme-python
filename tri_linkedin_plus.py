# tri_linkedin_plus.py
# Classement des contacts LinkedIn + génération prospects recommandés

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

INPUT_CSV = "Connections_from_LinkedIn.csv"

CSV_PROSPECTS = "prospects_recommandes.csv"
CSV_AUDIT = "audit_classification.csv"

SQLITE_DB = "prospects.db"
SQLITE_TABLE = "prospects"

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Texte en minuscule, sans espaces superflus."""
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    text = text.strip().lower()
    return re.sub(r"\s+", " ", text)

def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Trouve une colonne dont le nom contient un mot-clé parmi `candidates`."""
    lower_cols = {c.lower(): c for c in df.columns}
    for pattern in candidates:
        for lc, original in lower_cols.items():
            if pattern in lc:
                return original
    return None

def is_decision_maker(title: str) -> bool:
    """Heuristique pour repérer un décideur."""
    if not isinstance(title, str):
        return False

    t = normalize_text(title)

    patterns = [
        r"\b(gérant|gerant|co[- ]gérant|co[- ]gerant)\b",
        r"\b(dirigeant|dirigeante)\b",
        r"\b(fondateur|fondatrice|co[- ]fondateur|co[- ]fondatrice)\b",
        r"\b(président|présidente|president|presidente)\b",
        r"\b(ceo|coo|cto|cmo|cfo)\b",
        r"\b(owner|propriétaire)\b",
        r"chef d'entreprise",
        r"cheffe d'entreprise",
        r"\b(associé|associée|partner)\b",
        # Ajout de titres plus larges
        r"\b(manager|responsable|directeur|directrice|head|lead|co[- ]founder)\b",
    ]

    return any(re.search(rx, t, flags=re.IGNORECASE) for rx in patterns)

def detect_sector(text: str) -> str | None:
    """Détection très simple du secteur / type d'organisation."""
    if not isinstance(text, str):
        return None

    t = normalize_text(text)

    if re.search(r"\b(association|asso|ong|fondation)\b", t):
        return "association"
    if re.search(r"\b(artisan|artisanal|boulangerie|boucherie|coiffure|salon)\b", t):
        return "artisanat"
    if re.search(r"\b(commerce|boutique|magasin|retail|e[- ]commerce)\b", t):
        return "commerce"
    if re.search(r"\b(tpe|pme|micro[- ]entreprise|microentreprise)\b", t):
        return "tpe/pme"
    if re.search(r"\b(agence|studio|cabinet|conseil)\b", t):
        return "agence/cabinet"

    return None

# -------------------------------------------------------------------
# LOGIQUE D’EXCLUSION / SEGMENTATION
# -------------------------------------------------------------------

# 1) Exclusions dures : profils qu’on ne contactera jamais
EXCLUDE_PATTERNS: list[str] = [
    # Étudiants / alternants / stages
    r"\b(étudiant|etudiant|étudiante|etudiante)\b",
    r"\b(alternant|alternante|alternance)\b",
    r"\b(apprenti|apprentie)\b",
    r"\b(stagiaire|stage)\b",
    r"\b(intern|internship)\b",
    # RH / recrutement pur
    r"\b(talent acquisition|recruteur|recrutement|ressources humaines|rh)\b",
    # On ne bloque plus "junior", "bachelor", "licence", "master" pour laisser passer des profils potentiellement intéressants
]

# 2) Tech bloquée : dev salariés, stagiaires, juniors… qu’on ne veut pas
TECH_BLOCK_STRICT: list[str] = [
    r"\bstagiaire dev\b",
    r"\bjunior dev\b",
    r"\balternant dev\b",
    r"\betudiant dev\b",
    r"\bdeveloper intern\b",
    r"\bsoftware intern\b",
]

# 3) Tech qu’on accepte : freelance, agences, no-code, IA, automation…
TECH_ALLOWED: list[str] = [
    r"\b(freelance|indépendant|independant|consultant|consultante)\b",
    r"\b(agence|agency|studio|cabinet)\b",
    r"\b(no[- ]?code|nocode|automation|automatisation|ia|ai|ml|data)\b",
    r"\b(bubble|webflow|make\.com|zapier|n8n|wordpress|shopify)\b",
    r"\b(marketing|growth|seo|digital|communication)\b",  # ajout de mots-clés marketing/digital
]

def smart_exclude(row_text: str) -> bool:
    """Filtrage intelligent pour virer le tech non monétisable + profils non pertinents."""
    if not isinstance(row_text, str):
        row_text = "" if row_text is None else str(row_text)

    t = row_text.lower()

    # 1) Exclusion stricte (étudiants, alternants, RH, etc.)
    for rx in EXCLUDE_PATTERNS:
        if re.search(rx, t):
            return True

    # 2) Cas développeurs / data / tech très exécutant
    if any(word in t for word in ["developer", "développeur", "developpeur", " dev", "data ", "data engineer", "data scientist"]):
        # on exclut seulement si aucune indication business/freelance/agence/marketing ET pas de grade senior/lead/manager
        if not any(re.search(rx, t) for rx in TECH_ALLOWED) and not re.search(r"\b(senior|lead|manager|head|director)\b", t):
            return True

    # 3) Tech bloqués explicitement (stagiaire dev, junior dev, etc.)
    for rx in TECH_BLOCK_STRICT:
        if re.search(rx, t):
            return True

    # Sinon on garde
    return False

def classify_segment(row_text: str) -> str:
    """
    Retourne 'tech' ou 'business' pour affiner la com plus tard.
    """
    if not isinstance(row_text, str):
        row_text = "" if row_text is None else str(row_text)

    t = row_text.lower()

    # 1) Profils dev / data / ingénierie
    dev_patterns = [
        r"\b(developer|développeur|developpeur|devops|frontend|front[- ]end|backend|back[- ]end|fullstack|full[- ]stack)\b",
        r"\b(data engineer|data scientist|ml engineer)\b",
    ]
    if any(re.search(rx, t) for rx in dev_patterns):
        return "tech"

    # 2) Agences / studios web orientés digital
    agency_patterns = [r"\b(agence|agency|studio|web agency)\b"]
    web_markers = [
        r"\b(web|digital|numérique|seo|site|wordpress|shopify|e[- ]?commerce)\b",
    ]
    if any(re.search(rx, t) for rx in agency_patterns) and any(
        re.search(rx, t) for rx in web_markers
    ):
        return "tech"

    # 3) No-code / IA / automatisation
    nocode_patterns = [
        r"\b(no[- ]?code|nocode|bubble|webflow)\b",
        r"\b(make\.com|zapier|n8n)\b",
        r"\b(intelligence artificielle|ia|ai|automation|automatisation)\b",
    ]
    if any(re.search(rx, t) for rx in nocode_patterns):
        return "tech"

    # Par défaut : business classique
    return "business"

# -------------------------------------------------------------------
# PIPELINE PRINCIPAL
# -------------------------------------------------------------------

def main() -> None:
    path = Path(INPUT_CSV)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {INPUT_CSV}")

    # 1) Chargement CSV (tolérant au séparateur)
    print("=== DEBUG CHARGEMENT CSV ===")
    try:
        df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig", sep=";")

    print(f"Lignes : {len(df)}")
    print(f"Colonnes : {list(df.columns)}\n")

    # 2) Normalisation des colonnes importantes
    name_col = find_col(df, ["name", "nom"])
    title_col = find_col(df, ["title", "position", "occupation", "headline", "poste", "fonction"])
    url_col = find_col(df, ["url", "profile"])

    df["_name"] = df[name_col].astype(str) if name_col else ""
    df["_title"] = df[title_col].astype(str) if title_col else ""
    df["_url"] = df[url_col].astype(str) if url_col else ""

    # Ligne combinée pour les regex
    df["combined"] = (
        df["_name"].fillna("").astype(str)
        + " | "
        + df["_title"].fillna("").astype(str)
        + " | "
        + df["_url"].fillna("").astype(str)
    ).str.lower()

    # 3) Exclusions intelligentes (étudiants, stages, RH, tech non pertinent…)
    print("Application des règles d'exclusion brutes + smart_exclude...")

    mask_smart = df["combined"].apply(smart_exclude).astype(bool)

    df_excluded = df.loc[mask_smart].copy()
    df_kept = df.loc[~mask_smart].copy()

    print(f"Exclus (non-ciblés) : {len(df_excluded)}")
    print(f"Conservés           : {len(df_kept)}\n")

    # 3bis) Segment business / tech sur les lignes conservées
    print("Application du segment business/tech...")
    df_kept["segment"] = df_kept["combined"].apply(classify_segment)
    df_excluded["segment"] = df_excluded["combined"].apply(classify_segment)

    # 🔒 Standardisation du segment pour garantir uniquement 'business' ou 'tech'
    df_kept["segment"] = df_kept["segment"].apply(lambda x: "tech" if x == "tech" else "business")
    df_excluded["segment"] = df_excluded["segment"].apply(lambda x: "tech" if x == "tech" else "business")

    # 4) Décideur + secteur
    df_kept["decision_maker"] = df_kept["_title"].apply(is_decision_maker)
    df_kept["sector"] = df_kept["combined"].apply(detect_sector)

    # 5) Scoring "prospect recommandé" (affiné)
    #  - decision_maker : poids fort (2 points)
    #  - role_hit       : titres très intéressants (freelance, consultant, CEO, manager, etc.)
    #  - micro_hit      : petite structure / indépendant / agence / cabinet...

    role_hit = df_kept["_title"].str.contains(
        (
            r"(gérant|gerant|dirigeant|dirigeante|fondateur|fondatrice|"
            r"président|présidente|president|presidente|owner|"
            r"freelance|freelancer|indépendant|independant|"
            r"consultant|consultante|"
            r"entrepreneur|entrepreneure|entrepreneuse|"
            r"chef d'entreprise|cheffe d'entreprise|"
            r"co[- ]gérant|co[- ]gerant|co[- ]gérante|co[- ]gerante|"
            r"manager|responsable|directeur|directrice|head|lead)"
        ),
        case=False,
        na=False,
        regex=True,
    )

    micro_hit = df_kept["combined"].str.contains(
        (
            r"(tpe|pme|micro[- ]entreprise|microentreprise|"
            r"auto[- ]entrepreneur|autoentrepreneur|"
            r"artisan|artisanal|commerce|boutique|magasin|"
            r"agence|studio|cabinet)"
        ),
        case=False,
        na=False,
        regex=True,
    )

    df_kept["decision_maker"] = df_kept["decision_maker"].fillna(False)

    df_kept["score"] = (
        2 * df_kept["decision_maker"].astype(int)
        + 1 * role_hit.astype(int)
        + 1 * micro_hit.astype(int)
    )

    # Petit debug pour voir la réalité du scoring
    print("\n--- DEBUG SCORE ---")
    print("Distribution des scores (après filtrage) :")
    print(df_kept["score"].value_counts().sort_index())
    print()

    # Règle finale :
    # - recommandé si c'est un décideur détecté
    # - OU si score >= 1 (au moins un bon signal : rôle ou micro structure)
    df_kept["recommended"] = df_kept["decision_maker"] | (df_kept["score"] >= 1)

    # 6) Sorties propres
    out = df_kept.copy()
    out["name"] = df_kept["_name"].fillna("").str.strip()
    out["title"] = df_kept["_title"].fillna("").str.strip()
    out["url"] = df_kept["_url"].fillna("").str.strip()

    cols_out = ["name", "title", "sector", "segment", "recommended", "score", "url"]
    for c in cols_out:
        if c not in out.columns:
            out[c] = ""

    prospects_out = (
        out.loc[out["recommended"] == True, cols_out]  # noqa: E712
        .drop_duplicates(subset=["url"], keep="first")
        .sort_values(
            by=["recommended", "score", "segment", "sector", "title"],
            ascending=[False, False, True, True, True],
        )
    )

    prospects_out = prospects_out[prospects_out["url"] != ""]

    # 7) Audit (kept + excluded)
    df_excluded = df_excluded.copy()
    df_excluded["name"] = df_excluded["_name"].fillna("").str.strip()
    df_excluded["title"] = df_excluded["_title"].fillna("").str.strip()
    df_excluded["url"] = df_excluded["_url"].fillna("").str.strip()
    df_excluded["recommended"] = False
    df_excluded["sector"] = df_excluded["combined"].apply(detect_sector)
    df_excluded["score"] = 0
    df_excluded["decision_maker"] = False
    df_excluded["excluded"] = True

    audit_out = pd.concat(
        [
            prospects_out.assign(excluded=False),
            df_kept.loc[~df_kept["recommended"]].assign(
                name=df_kept["_name"].fillna("").str.strip(),
                title=df_kept["_title"].fillna("").str.strip(),
                url=df_kept["_url"].fillna("").str.strip(),
                excluded=False,
            )[cols_out + ["excluded"]],
            df_excluded[cols_out + ["excluded"]],
        ],
        ignore_index=True,
    )

    # 8) EXPORTS CSV
    print("\n--- EXPORTS CSV ---")
    prospects_out.to_csv(CSV_PROSPECTS, index=False, encoding="utf-8-sig")
    print(f"Prospects recommandés : {len(prospects_out)}  -> {CSV_PROSPECTS}")

    audit_out.to_csv(CSV_AUDIT, index=False, encoding="utf-8-sig")
    print(f"Audit classification  -> {CSV_AUDIT}")

    # --- EXPORT PAR SEGMENT ---
    prospects_business = prospects_out.loc[prospects_out["segment"] == "business"]
    prospects_tech = prospects_out.loc[prospects_out["segment"] == "tech"]

    prospects_business.to_csv("prospects_business.csv", index=False, encoding="utf-8-sig")
    prospects_tech.to_csv("prospects_tech.csv", index=False, encoding="utf-8-sig")

    print("\n--- EXPORT SEGMENTS ---")
    print(f"Business : {len(prospects_business)}  -> prospects_business.csv")
    print(f"Tech     : {len(prospects_tech)}      -> prospects_tech.csv")

    # 9) EXPORT SQLITE
    print("\n--- EXPORT SQLITE ---")
    con = sqlite3.connect(SQLITE_DB)
    cur = con.cursor()

    # On recrée la table à chaque exécution pour être sûr que le schéma est à jour
    cur.execute(f"DROP TABLE IF EXISTS {SQLITE_TABLE}")
    con.commit()

    to_insert = prospects_out.copy()
    to_insert["score"] = to_insert["score"].astype(int)
    to_insert["recommended"] = to_insert["recommended"].astype(int)

    to_insert.to_sql(SQLITE_TABLE, con, if_exists="replace", index=False)

    con.commit()
    con.close()

    # 10) Résumé
    print("\n-- Résumé classification --")
    print(f"Total contacts       : {len(df)}")
    print(f"Exclus (non-ciblés)  : {len(df_excluded)}")
    print(f"Conservés            : {len(df_kept)}")
    print(f"Prospects recommandés: {len(prospects_out)}")
    print("\nFichiers générés :")
    print(f" - Prospects recommandés : {CSV_PROSPECTS}")
    print(f" - Audit classification  : {CSV_AUDIT}")
    print(f" - SQLite                : {SQLITE_DB} (table {SQLITE_TABLE})")

if __name__ == "__main__":
    main()