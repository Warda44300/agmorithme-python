# wdc_api/security.py
# ===================
# Objectif :
# - Protéger les endpoints avec une clé API simple
# - Le client doit envoyer un header : X-API-Key: <valeur>

import os
from fastapi import Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(default=None)):
    """
    Dépendance FastAPI (middleware léger) :
    - Lit la clé reçue dans le header 'X-API-Key'
    - Compare avec la clé attendue côté serveur (variable d'environnement WDC_API_KEY)
    """

    # Clé attendue côté serveur (doit être définie avant de lancer l'API)
    expected = os.getenv("WDC_API_KEY")

    # Si le serveur n'a pas de clé configurée -> on refuse tout (sécurité)
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API serveur non configurée (WDC_API_KEY manquante).",
        )

    # Si la clé est absente ou mauvaise -> refus
    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante.",
        )
