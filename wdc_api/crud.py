# wdc_api/crud.py
# ===============
# Ce fichier regroupe les fonctions "métier" (CRUD) :
# Create / Read / Update / Delete sur la base de données.

from sqlalchemy.orm import Session

from wdc_api import models, schemas


def get_prospects(db: Session):
    """
    Récupère tous les prospects en base.
    """
    return db.query(models.Prospect).all()


def create_prospect(db: Session, prospect: schemas.ProspectCreate):
    """
    Crée un prospect en base à partir d'un schema ProspectCreate.
    """
    db_prospect = models.Prospect(
        name=prospect.name,
        title=prospect.title,
        sector=prospect.sector,
        url=prospect.url,
    )
    db.add(db_prospect)
    db.commit()
    db.refresh(db_prospect)
    return db_prospect
