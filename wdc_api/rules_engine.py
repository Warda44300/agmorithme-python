"""
wdc_api/rules_engine.py

Moteur de règles (règles déclaratives dans default.json).
But : appliquer des règles de filtrage/scoring sur un DataFrame.

Fix inclus :
- Matching insensible à la casse (CEO vs ceo)
- Matching insensible aux accents (président vs president)
- "contient" = vraie sous-chaîne (pas égalité stricte)
"""

from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd
import re
import unicodedata


def _norm_txt(v: Any) -> str:
    """Normalise un texte: str, minuscules, sans accents, espaces compactés."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s)
    return s


def _regex_mots_cles(mots_cles: List[str]) -> re.Pattern | None:
    """Compile une regex OR à partir des mots-clés normalisés."""
    cleaned = []
    for m in mots_cles or []:
        m2 = _norm_txt(m)
        if m2:
            cleaned.append(re.escape(m2))
    if not cleaned:
        return None
    return re.compile("(" + "|".join(cleaned) + ")")


def appliquer_regles(df: pd.DataFrame, config: Dict[str, Any], debug: bool = False) -> pd.DataFrame:
    """
    Applique config["regles"].

    Types:
    - contient_un_mot_cle:
        champ, mots_cles, action ("exclure" ou "score"), points
    - seuil:
        champ_score, min, action ("garder")

    Retour: df filtré + colonne score mise à jour.
    """
    regles = config.get("regles", [])
    if not isinstance(regles, list):
        raise ValueError("Configuration invalide: 'regles' doit être une liste")

    df_work = df.copy()

    # Colonne score
    if "score" not in df_work.columns:
        df_work["score"] = 0
    df_work["score"] = pd.to_numeric(df_work["score"], errors="coerce").fillna(0).astype(int)

    if debug:
        print("\n--- DEBUG REGLES ---")
        print(f"Lignes départ : {len(df_work)}")
        print(f"Colonnes dispo: {list(df_work.columns)}")

    for regle in regles:
        if not isinstance(regle, dict):
            continue

        regle_id = regle.get("id", "regle_sans_id")
        actif = bool(regle.get("actif", False))
        if not actif:
            if debug:
                print(f"[SKIP] {regle_id} (actif=false)")
            continue

        rtype = regle.get("type")

        # -----------------------------
        # 1) contient_un_mot_cle
        # -----------------------------
        if rtype == "contient_un_mot_cle":
            champ = regle.get("champ")
            if not champ or champ not in df_work.columns:
                if debug:
                    print(f"[WARN] {regle_id} champ introuvable: {champ}")
                continue

            mots_cles = regle.get("mots_cles", [])
            if not isinstance(mots_cles, list):
                mots_cles = []

            rx = _regex_mots_cles(mots_cles)
            if rx is None:
                if debug:
                    print(f"[WARN] {regle_id} aucun mot-clé valide")
                continue

            # NORMALISATION + contient(regex)
            serie_norm = df_work[champ].apply(_norm_txt)
            mask = serie_norm.str.contains(rx, na=False)

            action = regle.get("action")

            if action == "exclure":
                avant = len(df_work)
                df_work = df_work.loc[~mask].copy()
                apres = len(df_work)
                if debug:
                    print(f"[OK] {regle_id} exclure -> {avant} -> {apres} (retirés: {avant - apres})")

            elif action == "score":
                points = int(regle.get("points", 0))
                score_avant = int(df_work["score"].sum())
                df_work.loc[mask, "score"] = df_work.loc[mask, "score"] + points
                score_apres = int(df_work["score"].sum())
                if debug:
                    print(f"[OK] {regle_id} score +{points} -> score total {score_avant} -> {score_apres}")

            else:
                if debug:
                    print(f"[WARN] {regle_id} action inconnue: {action}")
                continue

        # -----------------------------
        # 2) seuil
        # -----------------------------
        elif rtype == "seuil":
            champ_score = regle.get("champ_score", "score")
            if champ_score not in df_work.columns:
                if debug:
                    print(f"[WARN] {regle_id} champ_score introuvable: {champ_score}")
                continue

            try:
                min_val = float(regle.get("min", 0))
            except Exception:
                min_val = 0.0

            action = regle.get("action")
            if action == "garder":
                avant = len(df_work)
                df_work = df_work.loc[df_work[champ_score] >= min_val].copy()
                apres = len(df_work)
                if debug:
                    print(f"[OK] {regle_id} garder {champ_score}>={min_val:g} -> {avant} -> {apres} (retirés: {avant - apres})")
            else:
                if debug:
                    print(f"[WARN] {regle_id} action inconnue (seuil): {action}")
                continue

        else:
            if debug:
                print(f"[WARN] {regle_id} type inconnu: {rtype}")
            continue

    if debug:
        print("--- FIN DEBUG ---\n")

    return df_work

