"""
wdc_api/routers/prospects.py
============================

Rôle :
- Déclarer les routes FastAPI liées aux prospects
- Protéger TOUTES ces routes avec une clé API via header "X-API-Key"
- Exposer cette protection dans OpenAPI pour que Swagger affiche "Authorize"

Pourquoi on utilise Security() et pas Depends() ?
- Depends() applique une dépendance, mais n'active pas toujours la déclaration OpenAPI "securitySchemes".
- Security() marque explicitement une dépendance de sécurité => Swagger affiche le cadenas + Authorize.
"""

from fastapi import APIRouter, Depends, Security
from sqlalchemy.orm import Session

from wdc_api.database import get_db
from wdc_api import crud, schemas
from wdc_api.security import require_api_key


# Router "prospects"
# - prefix="/prospects" => toutes les routes commencent par /prospects
# - tags=["prospects"]  => affichage propre dans Swagger /docs
router = APIRouter(
    prefix="/prospects",
    tags=["prospects"],
)


@router.get(
    "/",
    response_model=list[schemas.ProspectOut],
)
def list_prospects(
    # Sécurité :
    # - on appelle require_api_key via Security()
    # - ça force OpenAPI à déclarer un security scheme => bouton Authorize visible
    _: str = Security(require_api_key),

    # DB session :
    db: Session = Depends(get_db),
):
    """
    Endpoint : GET /prospects/

    Objectif :
    - Retourner la liste des prospects stockés en base

    Sécurité :
    - Header requis : X-API-Key: <ta_clé>
    - La clé doit matcher la variable d'environnement WDC_API_KEY

    Base de données :
    - db est une session SQLAlchemy fournie automatiquement par get_db()
    """
    return crud.get_prospects(db)
