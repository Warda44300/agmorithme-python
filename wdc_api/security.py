"""
wdc_api/security.py
===================

Rôle :
- Protéger les routes de l'API via une clé API envoyée dans un header HTTP
- Déclarer officiellement ce mécanisme dans OpenAPI, pour que Swagger affiche
  le bouton "Authorize" (cadenas) et permette de saisir la clé.

Header attendu :
- X-API-Key: <ta_clé>

Variable d'environnement requise :
- WDC_API_KEY
"""

import os

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

# Nom du header standardisé (Swagger/OpenAPI est sensible à la casse)
API_KEY_HEADER_NAME = "X-API-Key"

# Clé serveur attendue (stockée côté serveur via variable d'environnement)
SERVER_API_KEY = os.getenv("WDC_API_KEY")

# -------------------------------------------------------------------
# OPENAPI / SWAGGER
# -------------------------------------------------------------------
# Déclare un schéma de sécurité "API Key in header".
# -> C'est CET objet qui déclenche l'apparition du bouton "Authorize" dans /docs
# auto_error=False : on gère nous-mêmes l'erreur pour avoir des messages propres.
# -------------------------------------------------------------------

api_key_header = APIKeyHeader(
    name=API_KEY_HEADER_NAME,
    auto_error=False,
)

# -------------------------------------------------------------------
# DEPENDANCE A UTILISER DANS LES ROUTES
# -------------------------------------------------------------------
# Le router prospects fait déjà : Depends(require_api_key)
# Donc on garde ce nom.
# -------------------------------------------------------------------

def require_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dépendance FastAPI : vérifie que la clé API est fournie et valide.

    - Si WDC_API_KEY n'est pas définie côté serveur : 500 (mauvaise config serveur)
    - Si la clé envoyée est absente ou invalide : 401
    """
    # 1) Configuration serveur absente => erreur serveur
    if not SERVER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API serveur non configurée (WDC_API_KEY manquante).",
        )

    # 2) Clé manquante ou invalide => non autorisé
    if not api_key or api_key != SERVER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante.",
        )

    # 3) OK => on renvoie la clé (utile pour logs/traçabilité si besoin)
    return api_key

