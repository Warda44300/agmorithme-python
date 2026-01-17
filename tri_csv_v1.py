"""
tri_csv_v1.py

Script de tri / scoring sur un CSV (LinkedIn ou autre) basé sur une config JSON.

Objectifs :
- Lire un CSV (ex: export LinkedIn)
- Normaliser les colonnes selon un mapping défini dans wdc_api/configs/default.json
- Appliquer des règles (exclusion, scoring, seuil)
- Exporter un CSV filtré
- Afficher un mode DEBUG + statistiques (vides, distribution des scores, matches par règle)

Note importante :
- LinkedIn export classique : colonnes souvent "Name", "Title", "URL".
- Notre config doit mapper "poste" sur "Title" (pas "Name").
"""

from __future__ import annotations

import pandas as pd

from wdc_api.configs.loader import charger_configuration


def normaliser_colonnes(
    df: pd.DataFrame,
    config: dict,
    use_name_fallback: bool = True
) -> pd.DataFrame:
    """
    Crée des colonnes "logiques" standardisées à partir des colonnes réelles du CSV.

    Colonnes logiques créées :
    - nom
    - poste
    - url
    - entreprise
    - secteur
    - localisation

    Le mapping est défini dans config["champs_csv"].
    Exemple attendu :
      {
        "poste": "Title",
        "nom": "Name",
        "url": "URL",
        "entreprise": null,
        "secteur": null,
        "localisation": null
      }

    Si use_name_fallback=True :
    - si "poste" est vide, on met "nom" à la place (fallback),
      utile si certaines sources n'ont pas de titre.
    """
    mapping = config.get("champs_csv", {})
    df2 = df.copy()

    # 1) Normaliser le NOM d'abord (car "poste" peut fallback dessus)
    nom_col = mapping.get("nom")
    if nom_col and nom_col in df2.columns:
        df2["nom"] = df2[nom_col].fillna("").astype(str)
    else:
        df2["nom"] = ""

    # 2) Normaliser le POSTE
    poste_col = mapping.get("poste")
    if poste_col and poste_col in df2.columns:
        poste_series = df2[poste_col].fillna("").astype(str)
    else:
        # Si la colonne n'existe pas : on crée une série vide
        poste_series = pd.Series([""] * len(df2), index=df2.index)

    # Fallback : si poste vide => on utilise le nom (optionnel)
    if use_name_fallback:
        empty_mask = poste_series.str.strip() == ""
        if empty_mask.any():
            poste_series = poste_series.copy()
            poste_series.loc[empty_mask] = df2.loc[empty_mask, "nom"].fillna("").astype(str)

    df2["poste"] = poste_series

    # 3) Normaliser les autres colonnes logiques
    for col_logique in ["url", "entreprise", "secteur", "localisation"]:
        col_reelle = mapping.get(col_logique)
        if col_reelle and col_reelle in df2.columns:
            df2[col_logique] = df2[col_reelle].fillna("").astype(str)
        else:
            df2[col_logique] = ""

    return df2


def contient_un_mot_cle(valeur: str, mots_cles: list[str]) -> bool:
    """
    Retourne True si 'valeur' contient au moins un mot-clé (insensible à la casse).
    """
    v = (valeur or "").lower()
    for mot in mots_cles:
        if mot.lower() in v:
            return True
    return False


def appliquer_regles(
    df: pd.DataFrame,
    config: dict,
    debug: bool = True
) -> tuple[pd.DataFrame, dict]:
    """
    Applique config["regles"] dans l'ordre.

    Types supportés :
    - type="contient_un_mot_cle"
        - action="exclure" => supprime les lignes matchées
        - action="score"   => ajoute des points sur df["score"] pour les lignes matchées
    - type="seuil"
        - action="garder"  => garde uniquement les lignes dont score >= min

    Retour :
    - df_filtre
    - stats (résumé utile pour comprendre ce qui s'est passé)
    """
    df2 = df.copy()

    # On s'assure d'avoir une colonne score
    if "score" not in df2.columns:
        df2["score"] = 0

    regles = config.get("regles", [])

    stats = {
        "total_start": len(df2),
        "total_end": None,
        "score_min": None,
        "score_max": None,
        "score_nonzero": 0,
        "rules": [],
    }

    if debug:
        print("\n--- DEBUG REGLES ---")
        print("Lignes depart :", len(df2))
        print("Colonnes dispo:", df2.columns.tolist())

    # Application des règles dans l'ordre
    for r in regles:
        rid = r.get("id", "regle_sans_id")
        actif = r.get("actif", False)
        rtype = r.get("type")
        action = r.get("action")

        rule_stat = {
            "id": rid,
            "type": rtype,
            "action": action,
            "actif": actif,
            "matched": 0,
            "removed": 0,
            "kept": 0,
            "score_added": 0,
        }

        # Si la règle est désactivée, on ne fait rien
        if not actif:
            if debug:
                print(f"[SKIP] {rid} (actif=false)")
            stats["rules"].append(rule_stat)
            continue

        # --- Règles "contient_un_mot_cle" ---
        if rtype == "contient_un_mot_cle":
            champ = r.get("champ")
            mots_cles = r.get("mots_cles", [])

            # Si la colonne cible n'existe pas, on ignore
            if champ not in df2.columns:
                if debug:
                    print(f"[WARN] {rid} : champ '{champ}' absent -> aucune action.")
                stats["rules"].append(rule_stat)
                continue

            # Calcul du masque "match"
            mask_match = df2[champ].fillna("").astype(str).apply(
                lambda x: contient_un_mot_cle(x, mots_cles)
            )
            matched = int(mask_match.sum())
            rule_stat["matched"] = matched

            # Action : exclusion
            if action == "exclure":
                before = len(df2)
                df2 = df2[~mask_match].copy()
                removed = before - len(df2)
                rule_stat["removed"] = removed
                if debug:
                    print(f"[OK] {rid} exclure -> {before} -> {len(df2)} (retires: {removed})")

            # Action : scoring
            elif action == "score":
                points = int(r.get("points", 0))
                before_sum = df2["score"].sum()
                df2.loc[mask_match, "score"] = df2.loc[mask_match, "score"] + points
                after_sum = df2["score"].sum()
                rule_stat["score_added"] = int(after_sum - before_sum)
                if debug:
                    print(f"[OK] {rid} score +{points} -> score total {before_sum} -> {after_sum}")

            else:
                if debug:
                    print(f"[WARN] {rid} : action inconnue '{action}' -> ignoree.")

        # --- Règles de seuil ---
        elif rtype == "seuil":
            champ_score = r.get("champ_score", "score")
            min_score = r.get("min", None)

            if min_score is None:
                if debug:
                    print(f"[WARN] {rid} : min manquant -> ignore.")
                stats["rules"].append(rule_stat)
                continue

            if champ_score not in df2.columns:
                if debug:
                    print(f"[WARN] {rid} : champ_score '{champ_score}' absent -> ignore.")
                stats["rules"].append(rule_stat)
                continue

            # Action : garder score >= min
            if action == "garder":
                before = len(df2)
                mask_keep = df2[champ_score] >= float(min_score)
                kept = int(mask_keep.sum())
                df2 = df2[mask_keep].copy()
                removed = before - len(df2)
                rule_stat["kept"] = kept
                rule_stat["removed"] = removed
                if debug:
                    print(
                        f"[OK] {rid} garder score>={min_score} -> {before} -> {len(df2)} (retires: {removed})"
                    )
            else:
                if debug:
                    print(f"[WARN] {rid} : action seuil inconnue '{action}' -> ignoree.")

        else:
            if debug:
                print(f"[WARN] {rid} : type inconnu '{rtype}' -> ignore.")

        stats["rules"].append(rule_stat)

    if debug:
        print("--- FIN DEBUG ---\n")

    stats["total_end"] = len(df2)

    # Statistiques de score (sur le dataframe final)
    if "score" in df2.columns and len(df2) > 0:
        stats["score_min"] = float(df2["score"].min())
        stats["score_max"] = float(df2["score"].max())
        stats["score_nonzero"] = int((df2["score"] > 0).sum())

    return df2, stats


def compter_vides(series: pd.Series) -> int:
    """
    Compte le nombre de valeurs vides (après strip) dans une série (type string).
    """
    return int(series.fillna("").astype(str).str.strip().eq("").sum())


def afficher_resume_stats(stats: dict, df_raw: pd.DataFrame, df_norm: pd.DataFrame, config: dict) -> None:
    """
    Affiche un résumé :
    - vides dans les colonnes brutes importantes (Name/Title si présentes)
    - vides dans la colonne normalisée "poste"
    - score min/max / nb score>0
    - récap règle par règle : matches / suppressions / score ajouté
    """
    mapping = config.get("champs_csv", {})
    poste_col = mapping.get("poste")
    nom_col = mapping.get("nom")

    print("--- RESUME STATS ---")

    # Vides dans les colonnes brutes
    if poste_col and poste_col in df_raw.columns:
        empty_poste_raw = compter_vides(df_raw[poste_col])
        print(f"Colonne brute '{poste_col}' vides : {empty_poste_raw}")

    if nom_col and nom_col in df_raw.columns:
        empty_nom_raw = compter_vides(df_raw[nom_col])
        print(f"Colonne brute '{nom_col}' vides : {empty_nom_raw}")

    # Vides dans la colonne normalisée poste
    empty_poste_norm = compter_vides(df_norm["poste"])
    print(f"Colonne normalisee 'poste' vides : {empty_poste_norm}")

    # Distribution de score
    print("Score min :", stats.get("score_min"))
    print("Score max :", stats.get("score_max"))
    print("Score > 0 :", stats.get("score_nonzero"))

    # Résumé des règles
    for r in stats.get("rules", []):
        print(
            "- {id} | actif={actif} | type={type} | action={action} | matched={matched} | "
            "removed={removed} | kept={kept} | score_added={score_added}".format(
                id=r.get("id"),
                actif=r.get("actif"),
                type=r.get("type"),
                action=r.get("action"),
                matched=r.get("matched"),
                removed=r.get("removed"),
                kept=r.get("kept"),
                score_added=r.get("score_added"),
            )
        )

    print("--- FIN RESUME ---\n")


def main() -> None:
    """
    Point d'entrée :
    1) charger config
    2) lire CSV
    3) normaliser colonnes
    4) appliquer règles
    5) exporter CSV filtré
    6) afficher stats
    """
    config = charger_configuration()
    fichier_entree = "Connections_from_LinkedIn.csv"

    # Lecture CSV (utf-8-sig gère le BOM des exports LinkedIn)
    df = pd.read_csv(fichier_entree, encoding="utf-8-sig")

    # Normalisation
    df_norm = normaliser_colonnes(df, config, use_name_fallback=True)

    # Application des règles + debug
    df_filtre, stats = appliquer_regles(df_norm, config, debug=True)

    # Export CSV filtré
    fichier_sortie = "prospects_filtres_v1.csv"
    df_filtre.to_csv(fichier_sortie, index=False, encoding="utf-8-sig")

    print("OK. CSV filtre genere :", fichier_sortie)
    print("Lignes input :", len(df))
    print("Lignes output :", len(df_filtre))

    # Résumé statistique
    afficher_resume_stats(stats, df, df_norm, config)


if __name__ == "__main__":
    main()

  
