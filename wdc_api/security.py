"""
wdc_api/security.py
===================

Role :
- Proteger les routes de l'API via une cle API envoyee dans un header HTTP
- Declarer officiellement ce mecanisme dans OpenAPI, pour que Swagger affiche
  le bouton "Authorize" (cadenas) et permette de saisir la cle.

Header attendu :
- X-API-Key: <ta_cle>

Variable d'environnement requise :
- WDC_API_KEY
"""

import os
from dotenv import load_dotenv

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

# -------------------------------------------------------------------
# CHARGER LE FICHIER .env
# -------------------------------------------------------------------
# CRITIQUE : Sans cette ligne, WDC_API_KEY ne sera jamais chargee !
# -------------------------------------------------------------------
load_dotenv()

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

# Nom du header standardise (Swagger/OpenAPI est sensible a la casse)
API_KEY_HEADER_NAME = "X-API-Key"

# Cle serveur attendue (stockee cote serveur via variable d'environnement)
SERVER_API_KEY = os.getenv("WDC_API_KEY")

# -------------------------------------------------------------------
# OPENAPI / SWAGGER
# -------------------------------------------------------------------
# Declare un schema de securite "API Key in header".
# -> C'est CET objet qui declenche l'apparition du bouton "Authorize" dans /docs
# auto_error=False : on gere nous-memes l'erreur pour avoir des messages propres.
# -------------------------------------------------------------------

api_key_header = APIKeyHeader(
    name=API_KEY_HEADER_NAME,
    auto_error=False,
)

# -------------------------------------------------------------------
# DEPENDANCE A UTILISER DANS LES ROUTES
# -------------------------------------------------------------------
# Le router prospects fait deja : Depends(require_api_key)
# Donc on garde ce nom.
# -------------------------------------------------------------------

def require_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dependance FastAPI : verifie que la cle API est fournie et valide.

    - Si WDC_API_KEY n'est pas definie cote serveur : 500 (mauvaise config serveur)
    - Si la cle envoyee est absente ou invalide : 401
    
    Returns:
        str: La cle API validee
    """
    # 1) Configuration serveur absente => erreur serveur
    if not SERVER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cle API serveur non configuree (WDC_API_KEY manquante).",
        )

    # 2) Cle manquante ou invalide => non autorise
    if not api_key or api_key != SERVER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cle API invalide ou manquante.",
        )

    # 3) OK => on renvoie la cle (utile pour logs/tracabilite si besoin)
    return api_key
