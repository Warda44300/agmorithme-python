# 01_normalisation_linkedin.py
# ===========================
# Objectif
# --------
# Transformer un export LinkedIn "Connections" (colonnes souvent: Name, Title, URL)
# en un fichier "intermédiaire" standardisé, prêt pour l'enrichissement (Google Maps, scraping, etc.).
#
# Entrée  : Connections_from_LinkedIn.csv
# Sortie  : linkedin_normalise.csv
#
# Points importants
# -----------------
# - LinkedIn ne fournit généralement PAS l'entreprise, l'email, le tel... dans cet export.
# - Donc on crée des colonnes vides "prêtes à remplir" ensuite.
# - On garde le lien LinkedIn (clé principale) + le nom (utile pour recouper).
#
# Pré-requis
# ----------
# pip install pandas

from __future__ import annotations

import re
import pandas as pd


# -----------------------------
# Helpers (fonctions utilitaires)
# -----------------------------

def normaliser_nom_colonne(nom: str) -> str:
    """
    Normalise un nom de colonne pour le comparer facilement :
    - minuscules
    - trim espaces
    """
    return str(nom).strip().lower()


def trouver_colonne(df: pd.DataFrame, cible: str) -> str | None:
    """
    Trouve le nom réel d'une colonne dans le DataFrame, sans se faire piéger par la casse.
    Exemple: cible="url" matchera "URL" / "Url" / " url ".
    """
    cible_norm = normaliser_nom_colonne(cible)
    mapping = {normaliser_nom_colonne(c): c for c in df.columns}
    return mapping.get(cible_norm)


def split_prenom_nom(full_name: str) -> tuple[str, str]:
    """
    Sépare grossièrement "Prénom Nom" :
    - Si 1 mot -> prénom=mot, nom=""
    - Si plusieurs -> prénom=premier mot, nom=reste
    Note: on fera mieux plus tard si besoin (gestion particules, majuscules, etc.).
    """
    if full_name is None:
        return "", ""

    # Nettoyage simple (supprime espaces multiples)
    name = re.sub(r"\s+", " ", str(full_name).strip())
    if not name:
        return "", ""

    parts = name.split(" ")
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


# -----------------------------
# Script principal
# -----------------------------

def main() -> None:
    # 1) Fichier source LinkedIn
    fichier_entree = "Connections_from_LinkedIn.csv"

    # 2) Lecture du CSV
    # utf-8-sig est souvent nécessaire pour les exports avec BOM
    df = pd.read_csv(fichier_entree, encoding="utf-8-sig")

    # 3) Vérifier colonnes attendues (au moins Name + URL)
    col_name = trouver_colonne(df, "Name")
    col_url = trouver_colonne(df, "URL")

    if not col_name or not col_url:
        raise ValueError(
            "Colonnes requises introuvables dans le CSV.\n"
            f"Colonnes détectées: {list(df.columns)}\n"
            "Il faut au minimum: 'Name' et 'URL' (peu importe la casse)."
        )

    # 4) Construire le DataFrame normalisé
    #    -> colonnes standardisées pour la suite du pipeline
    output_rows = []

    for _, row in df.iterrows():
        full_name = row.get(col_name)
        linkedin_url = row.get(col_url)

        prenom, nom = split_prenom_nom(full_name)

        output_rows.append(
            {
                # Identité
                "prenom": prenom,
                "nom": nom,
                "nom_complet": "" if pd.isna(full_name) else str(full_name).strip(),

                # Clé principale (profil)
                "linkedin_url": "" if pd.isna(linkedin_url) else str(linkedin_url).strip(),

                # Champs enrichis plus tard (vides pour l’instant)
                "poste": "",
                "entreprise": "",
                "secteur": "",
                "email": "",
                "telephone": "",
                "site_web": "",
                "reseaux_sociaux": "",  # ex: Insta, Facebook, WhatsApp Business, etc.

                # Pilotage / traçabilité
                "source": "linkedin_connections_export",
                "statut": "a_enrichir",  # pratique pour suivre l'avancement
            }
        )

    df_out = pd.DataFrame(output_rows)

    # 5) Optionnel: supprimer les lignes sans URL LinkedIn (si jamais)
    # df_out = df_out[df_out["linkedin_url"].str.len() > 0].copy()

    # 6) Export
    fichier_sortie = "linkedin_normalise.csv"
    df_out.to_csv(fichier_sortie, index=False, encoding="utf-8-sig")

    # 7) Petit récap utile
    print("OK ✅ Fichier normalisé créé :", fichier_sortie)
    print("Lignes input  :", len(df))
    print("Lignes output :", len(df_out))
    print("Colonnes output :", list(df_out.columns))


if __name__ == "__main__":
    main()
