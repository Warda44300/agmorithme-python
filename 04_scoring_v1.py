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

from wdc_api.configs.loader import charger_configuration
from wdc_api.rules_engine import appliquer_regles_generiques


def main():
    """
    Point d'entrée du script.
    """

    # 1) Charger la configuration JSON
    config = charger_configuration()

    # 2) Définir le fichier d'entrée (CSV propre)
    #    -> Si tu changes de nom de fichier, modifie ici
    fichier_entree = "linkedin_propre_v1.csv"

    # 3) Lire le CSV
    #    encoding utf-8-sig pour gérer les CSV exportés avec BOM
    df = pd.read_csv(fichier_entree, encoding="utf-8-sig")

    # 4) Appliquer le moteur de règles générique
    #    -> df_score : dataframe final avec score / statuts
    #    -> stats : dictionnaire d'infos utiles pour debug
    df_score, stats = appliquer_regles_generiques(df, config)

    # 5) Export CSV scoré
    fichier_sortie = "linkedin_score_v1.csv"
    df_score.to_csv(fichier_sortie, index=False, encoding="utf-8-sig")

    # 6) Logs de contrôle
    print("OK ✅ Fichier scoré créé :", fichier_sortie)
    print("Lignes input :", len(df))
    print("Lignes gardées :", stats.get("gardes", "N/A"))
    print("Seuil prospect_min :", stats.get("seuil", "N/A"))
    print("Top 5 scores :", stats.get("top_scores", []))


if __name__ == "__main__":
    main()

