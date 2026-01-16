# wdc_api/schemas.py
# ==================
# Ce fichier contient les "schemas" Pydantic :
# -> ce sont les formats de données que l'API accepte (entrée)
# -> et ceux qu'elle renvoie (sortie)

from pydantic import BaseModel
from typing import Optional

class ProspectBase(BaseModel):
    """
    Champs communs (base) d'un prospect.
    """
    name: Optional[str] = None
    title: Optional[str] = None
    sector: Optional[str] = None
    url: str  # l'URL LinkedIn (on la veut obligatoire)

class ProspectCreate(ProspectBase):
    """
    Format attendu quand on veut CREER un prospect.
    Pour l'instant, même champs que la base.
    """
    pass

class ProspectOut(ProspectBase):
    """
    Format renvoyé par l'API (inclut l'id en base).
    """
    id: int

    class Config:
        # IMPORTANT (Pydantic v2) :
        # Autorise Pydantic à lire les objets SQLAlchemy comme des dicts
        from_attributes = True
