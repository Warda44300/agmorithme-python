# wdc_api/configs/loader.py
# =========================
# Ce fichier sert à charger et valider les fichiers de configuration JSON
# utilisés pour piloter les règles de tri (filtres, scoring, etc.)

import json
from pathlib import Path


def charger_configuration(chemin_config: str = "wdc_api/configs/default.json") -> dict:
    """
    Charge un fichier de configuration JSON et le retourne sous forme de dictionnaire Python.

    Paramètre :
    - chemin_config : chemin vers le fichier JSON de configuration

    Retour :
    - dict contenant toute la configuration

    Erreurs possibles :
    - FileNotFoundError : si le fichier n'existe pas
    - ValueError : si le JSON est invalide
    """

    # Conversion du chemin en objet Path (plus robuste et cross-platform)
    chemin = Path(chemin_config)

    # Vérification de l'existence du fichier
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable : {chemin}")

    try:
        # Ouverture et lecture du fichier JSON
        with open(chemin, "r", encoding="utf-8") as fichier:
            configuration = json.load(fichier)

    except json.JSONDecodeError as erreur:
        # Erreur si le JSON est mal formé
        raise ValueError(f"Erreur de format JSON dans {chemin} : {erreur}")

    # Vérification minimale de structure (sécurité)
    if "filtres" not in configuration:
        raise ValueError("Configuration invalide : clé 'filtres' manquante")

    if "scoring" not in configuration:
        raise ValueError("Configuration invalide : clé 'scoring' manquante")
    print("CONFIG FILE LOADED =", chemin_config)
    print("CONFIG KEYS =", list(configuration.keys()))

    # Si tout est OK, on retourne la configuration complète
    return configuration
