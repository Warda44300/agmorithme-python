# 03_dedoublonnage_qualite.py
# ===========================
# Objectif
# --------
# - Charger linkedin_normalise_enrichi_min.csv
# - Vérifier la qualité (valeurs vides, doublons)
# - Dédoublonner sur linkedin_slug (clé stable)
# - Exporter un CSV propre pour la suite (scoring / enrichissement business)
#
# Entrée  : linkedin_normalise_enrichi_min.csv
# Sortie  : linkedin_propre_v1.csv

from __future__ import annotations

import pandas as pd
import sys


def main() -> None:
    fichier_entree = "linkedin_normalise_enrichi_min.csv"
    fichier_sortie = "linkedin_propre_v1.csv"
    if len(sys.argv) > 1 and sys.argv[1].strip():
        fichier_entree = sys.argv[1].strip()

    print(f"[INFO] Fichier d'entrée : {fichier_entree}")
    df = pd.read_csv(fichier_entree, encoding="utf-8-sig")

    # Sécurité : colonnes indispensables
    indispensables = ["linkedin_url", "linkedin_slug"]
    for col in indispensables:
        if col not in df.columns:
            raise ValueError(f"Colonne obligatoire manquante : {col}")

    # Indicateurs qualité
    nb_lignes = len(df)
    slug_vides = int((df["linkedin_slug"].fillna("") == "").sum())
    taux_slug_vides = (slug_vides / nb_lignes) * 100 if nb_lignes else 0.0

    # Doublons sur slug (on garde le 1er)
    nb_doublons = int(df.duplicated(subset=["linkedin_slug"]).sum())

    df_propre = df.drop_duplicates(subset=["linkedin_slug"], keep="first").copy()

    # Export
    df_propre.to_csv(fichier_sortie, index=False, encoding="utf-8-sig")

    # Reporting clair
    print("OK ✅ Fichier propre créé :", fichier_sortie)
    print("Lignes input :", nb_lignes)
    print("Lignes output :", len(df_propre))
    print("Doublons linkedin_slug supprimés :", nb_doublons)
    print("Slug vides :", slug_vides)
    print("Taux slug vides :", f"{taux_slug_vides:.2f}%")
    print("Colonnes output :", list(df_propre.columns))


if __name__ == "__main__":
    main()
