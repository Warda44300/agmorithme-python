# 02_enrichissement_minimal.py
# ============================
# Objectif
# --------
# Ajouter des infos "minimum viable" à linkedin_normalise.csv sans scraping :
# - linkedin_slug : identifiant du profil dans l'URL (utile comme clé stable)
# - nettoyer/normaliser linkedin_url
# - préparer des colonnes "futures" (ex: entreprise_detectee) si besoin
#
# Entrée  : linkedin_normalise.csv
# Sortie  : linkedin_normalise_enrichi_min.csv

from __future__ import annotations

import re
import pandas as pd
import sys


def nettoyer_url(url: str) -> str:
    """
    Nettoie une URL LinkedIn :
    - None/NaN -> ""
    - trim
    - supprime les paramètres ?xxx
    - supprime le slash final (optionnel mais pratique)
    """
    if url is None or (isinstance(url, float) and pd.isna(url)):
        return ""

    u = str(url).strip()

    # Enlève paramètres
    u = u.split("?")[0].strip()

    # Enlève slash final
    if u.endswith("/"):
        u = u[:-1]

    return u


def extraire_slug_linkedin(url: str) -> str:
    """
    Extrait le "slug" LinkedIn depuis une URL.
    Ex:
    - https://www.linkedin.com/in/jean-dupont-12345 -> jean-dupont-12345
    - https://linkedin.com/in/jean-dupont-12345 -> jean-dupont-12345
    Sinon -> ""
    """
    u = nettoyer_url(url)
    if not u:
        return ""

    # Patterns principaux
    # /in/<slug>
    m = re.search(r"linkedin\.com/in/([^/]+)$", u)
    if m:
        return m.group(1)

    # Parfois LinkedIn renvoie des urls un peu différentes, on garde une version "best effort"
    return ""


def main() -> None:
    fichier_entree = "linkedin_normalise.csv"
    fichier_sortie = "linkedin_normalise_enrichi_min.csv"
    if len(sys.argv) > 1 and sys.argv[1].strip():
        fichier_entree = sys.argv[1].strip()

    df = pd.read_csv(fichier_entree, encoding="utf-8-sig")
    lignes_input = len(df)

    # Sécurités : colonnes indispensables
    if "linkedin_url" not in df.columns:
        raise ValueError("Colonne 'linkedin_url' introuvable dans linkedin_normalise.csv")

    # Nettoyage URL + extraction slug
    df["linkedin_url"] = df["linkedin_url"].apply(nettoyer_url)
    df["linkedin_slug"] = df["linkedin_url"].apply(extraire_slug_linkedin)

    # Sécurité first (data-only) : garantir les colonnes si absentes
    if "action_linkedin_autorisee" not in df.columns:
        df["action_linkedin_autorisee"] = "non"
    if "validated_by" not in df.columns:
        df["validated_by"] = ""
    if "validated_at" not in df.columns:
        df["validated_at"] = ""
    if "interdit_action" not in df.columns:
        df["interdit_action"] = "oui"

    # Statut plus précis
    df["statut"] = df["linkedin_slug"].apply(lambda s: "a_enrichir" if s else "url_invalide_ou_absente")

    # Contrat de sortie : ordre des colonnes figé (entrée + linkedin_slug)
    colonnes_sortie = [c for c in df.columns if c != "linkedin_slug"] + ["linkedin_slug"]
    df = df[colonnes_sortie]

    # Export
    df.to_csv(fichier_sortie, index=False, encoding="utf-8-sig")

    print("OK Fichier enrichi minimal créé :", fichier_sortie)
    print("Lignes input :", lignes_input)
    print("Lignes output :", len(df))
    print("Colonnes output :", list(df.columns))
    print("Slug vides :", int((df["linkedin_slug"] == "").sum()))
    print("Slug non vides :", int((df["linkedin_slug"] != "").sum()))


if __name__ == "__main__":
    main()
