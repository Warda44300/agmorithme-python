"""
tri_csv_v1.py
-------------
Script de tri CSV (LinkedIn ou autres) basé sur une config JSON.

Objectif :
- Lire un CSV
- Normaliser les colonnes selon config["champs_csv"]
- Appliquer des règles (config["regles"])
- Exporter un CSV filtré

+ Mode DEBUG : affiche combien de lignes restent après chaque règle
"""

from __future__ import annotations

import pandas as pd

from wdc_api.configs.loader import charger_configuration


def normaliser_colonnes(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Crée des colonnes logiques (poste, url, entreprise, secteur, localisation)
    à partir des colonnes réelles du CSV (ex: Title, URL...).

    Si une colonne n'existe pas dans le CSV, on la crée vide.
    """
    mapping = config.get("champs_csv", {})
    df2 = df.copy()

    # On va créer des colonnes "logiques" standardisées
    colonnes_logiques = ["poste", "url", "entreprise", "secteur", "localisation"]

    for col_logique in colonnes_logiques:
        col_reelle = mapping.get(col_logique)

        # Si la config met null / None / "" => on crée une colonne vide
        if not col_reelle:
            df2[col_logique] = ""
            continue

        # Si la colonne réelle existe, on la copie
        if col_reelle in df2.columns:
            df2[col_logique] = df2[col_reelle].fillna("").astype(str)
        else:
            # Sinon on crée vide (au lieu de crasher)
            df2[col_logique] = ""

    return df2


def contient_un_mot_cle(valeur: str, mots_cles: list[str]) -> bool:
    """
    Retourne True si 'valeur' contient un des mots-clés (insensible à la casse).
    """
    v = (valeur or "").lower()
    for mot in mots_cles:
        if mot.lower() in v:
            return True
    return False


def appliquer_regles(df: pd.DataFrame, config: dict, debug: bool = True) -> pd.DataFrame:
    """
    Applique config["regles"] dans l'ordre.

    Types gérés :
    - contient_un_mot_cle + action=exclure
    - contient_un_mot_cle + action=score
    - seuil + action=garder

    DEBUG : affiche le nombre de lignes après chaque règle.
    """
    df2 = df.copy()

    # Score initial
    if "score" not in df2.columns:
        df2["score"] = 0

    regles = config.get("regles", [])

    if debug:
        print("\n--- DEBUG REGLES ---")
        print("Lignes départ :", len(df2))
        print("Colonnes dispo:", df2.columns.tolist())

    for r in regles:
        rid = r.get("id", "regle_sans_id")
        actif = r.get("actif", False)

        if not actif:
            if debug:
                print(f"[SKIP] {rid} (actif=false)")
            continue

        rtype = r.get("type")
        action = r.get("action")

        # 1) contient_un_mot_cle
        if rtype == "contient_un_mot_cle":
            champ = r.get("champ")  # ex: "poste"
            mots_cles = r.get("mots_cles", [])

            if champ not in df2.columns:
                # Tolérance : si la colonne n'existe pas, on ne fait rien
                if debug:
                    print(f"[WARN] {rid} : champ '{champ}' absent -> aucune action.")
                continue

            mask_match = df2[champ].fillna("").astype(str).apply(lambda x: contient_un_mot_cle(x, mots_cles))

            if action == "exclure":
                avant = len(df2)
                df2 = df2[~mask_match].copy()
                if debug:
                    print(f"[OK] {rid} exclure -> {avant} -> {len(df2)} (retirés: {avant - len(df2)})")

            elif action == "score":
                points = int(r.get("points", 0))
                avant_score = df2["score"].sum()
                df2.loc[mask_match, "score"] = df2.loc[mask_match, "score"] + points
                apres_score = df2["score"].sum()
                if debug:
                    print(f"[OK] {rid} score +{points} -> score total {avant_score} -> {apres_score}")

            else:
                if debug:
                    print(f"[WARN] {rid} : action inconnue '{action}' -> ignorée.")

        # 2) seuil
        elif rtype == "seuil":
            champ_score = r.get("champ_score", "score")
            min_score = r.get("min", None)

            # Si min absent => on ignore
            if min_score is None:
                if debug:
                    print(f"[WARN] {rid} : min manquant -> ignoré.")
                continue

            # Si la colonne score n'existe pas => on ignore (au lieu de vider)
            if champ_score not in df2.columns:
                if debug:
                    print(f"[WARN] {rid} : champ_score '{champ_score}' absent -> ignoré.")
                continue

            if action == "garder":
                avant = len(df2)
                df2 = df2[df2[champ_score] >= float(min_score)].copy()
                if debug:
                    print(f"[OK] {rid} garder score>={min_score} -> {avant} -> {len(df2)} (retirés: {avant - len(df2)})")
            else:
                if debug:
                    print(f"[WARN] {rid} : action seuil inconnue '{action}' -> ignorée.")

        else:
            if debug:
                print(f"[WARN] {rid} : type inconnu '{rtype}' -> ignoré.")

    if debug:
        print("--- FIN DEBUG ---\n")

    return df2


def main() -> None:
    """
    Point d'entrée :
    - charge config
    - lit CSV
    - normalise colonnes
    - applique règles
    - export CSV final
    """
    config = charger_configuration()
    fichier_entree = "Connections_from_LinkedIn.csv"

    # Lecture CSV : utf-8-sig pour gérer BOM souvent présent sur exports
    df = pd.read_csv(fichier_entree, encoding="utf-8-sig")

    # Normalisation colonnes selon mapping
    df_norm = normaliser_colonnes(df, config)

    # Application règles + debug
    df_filtre = appliquer_regles(df_norm, config, debug=True)

    # Export
    fichier_sortie = "prospects_filtres_v1.csv"
    df_filtre.to_csv(fichier_sortie, index=False, encoding="utf-8-sig")

    print("OK ✅ CSV filtré généré :", fichier_sortie)
    print("Lignes input :", len(df))
    print("Lignes output :", len(df_filtre))


if __name__ == "__main__":
    main()

  
