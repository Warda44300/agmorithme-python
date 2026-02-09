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
import sys
import os


# -----------------------------
# Helpers (fonctions utilitaires)
# -----------------------------

def normaliser_nom_colonne(nom: str) -> str:
    """
    Normalise un nom de colonne pour le comparer facilement :
    - minuscules
    - trim espaces
    - remplace espaces et tirets par underscores
    - compactage underscores multiples
    """
    n = str(nom).strip().lower()
    n = re.sub(r"[\s\-]+", "_", n)
    n = re.sub(r"_+", "_", n)
    return n


def trouver_colonne(mapping: dict[str, str], cible: str) -> str | None:
    """
    Trouve le nom réel d'une colonne dans le mapping normalisé.
    Exemple: cible="url" matchera "URL" / "Url" / " url ".
    """
    return mapping.get(normaliser_nom_colonne(cible))


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
    if len(sys.argv) > 1 and sys.argv[1].strip():
        fichier_entree = sys.argv[1].strip()

    # 2) Lecture du CSV
    # utf-8-sig est souvent nécessaire pour les exports avec BOM
    print(f"[INFO] Fichier d'entrée : {fichier_entree}")
    if not os.path.isfile(fichier_entree):
        cwd = os.getcwd()
        csv_files = sorted(
            [f for f in os.listdir(cwd) if f.lower().endswith(".csv")]
        )[:10]
        print(
            "ERREUR : fichier introuvable.\n"
            f"- Fichier recherché : {fichier_entree}\n"
            f"- Dossier courant : {cwd}\n"
            f"- CSV présents (max 10) : {csv_files if csv_files else 'aucun'}\n"
            "Usage : python 01_normalisation_linkedin.py <fichier.csv>"
        )
        sys.exit(1)
    df = pd.read_csv(fichier_entree, encoding="utf-8-sig")

    # 3) Mapping colonnes normalisées -> colonnes originales
    mapping = {normaliser_nom_colonne(c): c for c in df.columns}

    # Logs de diagnostic (légers)
    print("Colonnes détectées (normalisées) :", list(mapping.keys()))
    print("Colonnes originales :", list(df.columns))
    print("Nombre de lignes lues :", len(df))

    # 4) Vérifier colonnes attendues (au minimum url)
    col_url = trouver_colonne(mapping, "url")
    if not col_url:
        # Alias minimal compatible
        col_url = trouver_colonne(mapping, "linkedin_url")

    if not col_url:
        print(
            "ERREUR : colonne minimale manquante : 'url'.\n"
            f"Colonnes détectées (normalisées): {list(mapping.keys())}"
        )
        sys.exit(1)

    # Optionnel : nom si présent (pas obligatoire)
    col_name = trouver_colonne(mapping, "name")

    # 5) Construire le DataFrame normalisé
    #    -> colonnes standardisées pour la suite du pipeline
    output_rows = []

    for _, row in df.iterrows():
        full_name = row.get(col_name) if col_name else ""
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

                # Sécurité first (data-only)
                "action_linkedin_autorisee": "non",
                "validated_by": "",
                "validated_at": "",
                "interdit_action": "oui",
            }
        )

    df_out = pd.DataFrame(output_rows)

    # Contrat de sortie : ordre des colonnes figé
    colonnes_sortie = [
        "prenom",
        "nom",
        "nom_complet",
        "linkedin_url",
        "poste",
        "entreprise",
        "secteur",
        "email",
        "telephone",
        "site_web",
        "reseaux_sociaux",
        "source",
        "statut",
    ]
    df_out = df_out[colonnes_sortie]

    # 6) Optionnel: supprimer les lignes sans URL LinkedIn (si jamais)
    # df_out = df_out[df_out["linkedin_url"].str.len() > 0].copy()

    # 7) Export
    fichier_sortie = "linkedin_normalise.csv"
    df_out.to_csv(fichier_sortie, index=False, encoding="utf-8-sig")

    # 8) Petit récap utile
    print("OK Fichier normalisé créé :", fichier_sortie)
    print("Lignes input  :", len(df))
    print("Lignes output :", len(df_out))
    print("Colonnes output :", list(df_out.columns))


if __name__ == "__main__":
    main()
