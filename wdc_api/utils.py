# app/utils.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from wdc_api.models import Prospect


def compute_stats(db: Session):
    """
    Calcule quelques statistiques de base sur les prospects.
    Renvoie un dictionnaire avec le total, les comptes par secteur, et le nombre d'e‑mails renseignés.
    """
    # Total de lignes dans la table
    total = db.query(func.count(Prospect.id)).scalar()
    # Comptage des prospects par secteur, retourné sous forme de dictionnaire { secteur: nb }
    seg_counts = dict(
        db.query(Prospect.sector, func.count(Prospect.id))
        .group_by(Prospect.sector)
        .all()
    )
    # Nombre de prospects ayant une adresse e‑mail renseignée
    with_email = db.query(func.count(Prospect.id))\
                   .filter(Prospect.email != None).scalar()  # noqa (ignore l'avertissement pylint)
    return {
        "total": total,
        "par_secteur": seg_counts,
        "emails_connus": with_email,
    }
