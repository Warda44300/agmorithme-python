# 04_scoring_v1.py
# =========================
# Objectif :
# - Lire le CSV "propre" (après normalisation + enrichissement minimal + dédoublonnage)
# - Charger la config JSON (default.json)
# - Appliquer le moteur de règles générique (rules_engine)
# - Exporter un CSV scoré (linkedin_score_v1.csv)
#
# Résultat attendu :
# - Un fichier linkedin_score_v1.csv avec une colonne "score" (et éventuellement d'autres colonnes de debug)
# - Un petit résumé dans le terminal (lignes gardées, top scores, etc.)

import pandas as pd
import os
import sys

from wdc_api.configs.loader import charger_configuration
from wdc_api.rules_engine import appliquer_regles, _norm_txt, _regex_mots_cles


def main():
    """
    Point d'entrée du script.
    """

    def expliquer_regles(df: pd.DataFrame, config: dict) -> dict:
        regles = config.get("regles", [])
        if not isinstance(regles, list):
            regles = []

        df_work = df.copy()
        if "score" not in df_work.columns:
            df_work["score"] = 0
        df_work["score"] = pd.to_numeric(df_work["score"], errors="coerce").fillna(0).astype(int)

        raisons = []
        apres_filtres = None

        for regle in regles:
            if not isinstance(regle, dict):
                continue
            regle_id = regle.get("id", "regle_sans_id")
            if not bool(regle.get("actif", False)):
                continue

            rtype = regle.get("type")
            if rtype == "contient_un_mot_cle":
                champ = regle.get("champ")
                if not champ or champ not in df_work.columns:
                    continue
                mots_cles = regle.get("mots_cles", [])
                if not isinstance(mots_cles, list):
                    mots_cles = []
                rx = _regex_mots_cles(mots_cles)
                if rx is None:
                    continue
                serie_norm = df_work[champ].apply(_norm_txt)
                mask = serie_norm.str.contains(rx, na=False)
                action = regle.get("action")
                if action == "exclure":
                    avant = len(df_work)
                    df_work = df_work.loc[~mask].copy()
                    apres = len(df_work)
                    removed = avant - apres
                    if removed > 0:
                        raisons.append((regle_id, removed))
                elif action == "score":
                    points = int(regle.get("points", 0))
                    df_work.loc[mask, "score"] = df_work.loc[mask, "score"] + points

            elif rtype == "seuil":
                champ_score = regle.get("champ_score", "score")
                if champ_score not in df_work.columns:
                    continue
                try:
                    min_val = float(regle.get("min", 0))
                except Exception:
                    min_val = 0.0
                action = regle.get("action")
                if action == "garder":
                    if apres_filtres is None:
                        apres_filtres = len(df_work)
                    avant = len(df_work)
                    df_work = df_work.loc[df_work[champ_score] >= min_val].copy()
                    apres = len(df_work)
                    removed = avant - apres
                    if removed > 0:
                        raisons.append((f"seuil_{regle_id}", removed))

        if apres_filtres is None:
            apres_filtres = len(df_work)

        raisons.sort(key=lambda x: x[1], reverse=True)
        return {
            "apres_filtres": apres_filtres,
            "apres_seuil": len(df_work),
            "raisons": raisons[:10],
        }

    # 0) Fichier de config (valeur par défaut du loader)
    fichier_config = "wdc_api/configs/default.json"
    if not os.path.isfile(fichier_config):
        print(
            "ERREUR : fichier de configuration introuvable.\n"
            f"- Fichier attendu : {fichier_config}\n"
            f"- Dossier courant : {os.getcwd()}\n"
            "Usage : python 04_scoring_v1.py <fichier.csv>"
        )
        sys.exit(1)

    # 1) Charger la configuration JSON
    config = charger_configuration(fichier_config)

    # 2) Définir le fichier d'entrée (CSV propre)
    #    -> Si tu changes de nom de fichier, modifie ici
    fichier_entree = "linkedin_propre_v1.csv"
    explain = ("--explain" in sys.argv) or ("--debug" in sys.argv)
    args_pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args_pos) > 0 and args_pos[0].strip():
        fichier_entree = args_pos[0].strip()
    print(f"[INFO] Fichier d'entrée : {fichier_entree}")

    # 3) Lire le CSV
    #    encoding utf-8-sig pour gérer les CSV exportés avec BOM
    df = pd.read_csv(fichier_entree, encoding="utf-8-sig")
    lignes_input = len(df)

    if explain:
        diag = expliquer_regles(df, config)
        print("[EXPLAIN] Lignes après lecture :", lignes_input)
        print("[EXPLAIN] Lignes après filtres :", diag["apres_filtres"])
        print("[EXPLAIN] Lignes après scoring + seuil :", diag["apres_seuil"])

    # 4) Appliquer le moteur de règles générique
    #    -> df_score : dataframe final avec score / statuts
    #    -> stats : dictionnaire d'infos utiles pour debug
    resultat = appliquer_regles(df, config)
    if isinstance(resultat, tuple) and len(resultat) == 2:
        df_score, stats = resultat
    else:
        df_score = resultat
        stats = {}

    # 4b) Garantir colonnes minimales
    if "score" not in df_score.columns:
        df_score["score"] = 0

    seuil = stats.get("seuil")
    if seuil is None:
        try:
            seuil = float(config.get("scoring", {}).get("seuils", {}).get("prospect_min", 0))
        except Exception:
            seuil = 0

    if "decision" not in df_score.columns:
        df_score["decision"] = df_score["score"].apply(lambda s: "keep" if s >= seuil else "discard")

    # 5) Export CSV scoré
    fichier_sortie = "linkedin_score_v1.csv"
    df_score.to_csv(fichier_sortie, index=False, encoding="utf-8-sig")

    # 6) Logs de contrôle
    print("OK ✅ Fichier scoré créé :", fichier_sortie)
    print("Lignes input :", lignes_input)
    print("Lignes output :", len(df_score))
    scores = pd.to_numeric(df_score["score"], errors="coerce").fillna(0)
    if len(df_score) == 0:
        print("Scores (min/max/moy) :", "0/0/0")
    else:
        print("Scores (min/max/moy) :", f"{scores.min():.0f}/{scores.max():.0f}/{scores.mean():.2f}")
    keep_count = int((df_score["decision"] == "keep").sum())
    discard_count = int((df_score["decision"] == "discard").sum())
    print("Keep / Discard :", keep_count, "/", discard_count)
    print("Colonnes output :", list(df_score.columns))

    if explain:
        print("[EXPLAIN] Seuil utilisé :", seuil)
        print("[EXPLAIN] Top 10 raisons d'exclusion :")
        for rid, cnt in diag["raisons"]:
            print(f"  - {rid} : {cnt}")


if __name__ == "__main__":
    main()

