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
from wdc_api.rules_engine import appliquer_regles


def main():
    """
    Point d'entrée du script.
    """

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
    if len(sys.argv) > 1 and sys.argv[1].strip():
        fichier_entree = sys.argv[1].strip()
    print(f"[INFO] Fichier d'entrée : {fichier_entree}")

    # 3) Lire le CSV
    #    encoding utf-8-sig pour gérer les CSV exportés avec BOM
    df = pd.read_csv(fichier_entree, encoding="utf-8-sig")
    lignes_input = len(df)

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


if __name__ == "__main__":
    main()

