# wdc_api/routers/prospects.py
# ============================
# Rôle :
# - Déclarer les routes (endpoints) FastAPI liées aux prospects
# - Protéger TOUTES ces routes avec une clé API (header x-api-key)
# - Appeler la couche CRUD pour récupérer les données en base PostgreSQL

from fastapi import APIRouter, Depends  # APIRouter = regroupe des routes / Depends = injection de dépendances
from sqlalchemy.orm import Session      # Type de session SQLAlchemy (connexion DB côté Python)

from wdc_api.database import get_db            # Donne une session DB par requête et la ferme proprement
from wdc_api import crud, schemas              # crud = logique DB / schemas = format des réponses API
from wdc_api.security import require_api_key   # Dépendance de sécurité : vérifie la clé API


# Création du "router" prospects :
# - prefix="/prospects" => toutes les routes ici commenceront par /prospects
# - tags=["prospects"]  => affichage propre dans Swagger /docs
# - dependencies=[...]  => applique require_api_key à TOUTES les routes du router (sécurité globale)
router = APIRouter(
    prefix="/prospects",
    tags=["prospects"],
    dependencies=[Depends(require_api_key)]  # 🔐 Protection globale par clé API
)


@router.get(
    "/",  # Chemin final => /prospects/
    response_model=list[schemas.ProspectOut]  # Format de sortie (liste de prospects)
)
def list_prospects(db: Session = Depends(get_db)):
    """
    Endpoint : GET /prospects/

    Objectif :
    - Retourner la liste des prospects stockés en base

    Sécurité :
    - La route est protégée par la dépendance globale du router :
      require_api_key() vérifie que le header "x-api-key" correspond à la clé serveur.

    Base de données :
    - db est une session SQLAlchemy fournie automatiquement par get_db()
    """
    # Appel à la couche CRUD qui interroge la table prospects et renvoie les lignes
    return crud.get_prospects(db)

