"""
models.py
---------

Responsabilité :
- Définir les modèles SQLAlchemy (tables) de l'application.

Note :
- Ce fichier est importé avant Base.metadata.create_all()
- Les modèles doivent hériter de Base (déclarative_base) défini dans database.py
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from .database import Base


class Prospect(Base):
    """
    Table : prospects

    Stocke les prospects issus de LinkedIn (ou d'autres sources à terme).
    """

    # Nom de la table en base
    __tablename__ = "prospects"

    # ---------------------------------------------------------------------
    # Colonnes principales
    # ---------------------------------------------------------------------

    # Clé primaire : identifiant auto-incrémenté
    id = Column(Integer, primary_key=True, index=True)

    # Informations prospect
    name = Column(Text, nullable=True)    # Nom
    title = Column(Text, nullable=True)   # Poste / titre
    sector = Column(Text, nullable=True)  # Secteur

    # URL LinkedIn (ou autre URL de profil) : unique + indexée
    # String(500) évite les surprises si l'URL est longue.
    url = Column(String(500), unique=True, nullable=False, index=True)

    # Coordonnées (facultatives)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Localisation (facultative)
    address = Column(Text, nullable=True)
    city = Column(String(120), nullable=True)
    country = Column(String(120), nullable=True)

    # Source des données
    # default=... applique la valeur côté Python
    # server_default=... applique la valeur côté PostgreSQL (plus robuste)
    source = Column(String(50), nullable=False, default="linkedin", server_default="linkedin")

    # ---------------------------------------------------------------------
    # Timestamps
    # ---------------------------------------------------------------------

    # Date de création (définie par PostgreSQL au moment de l'insert)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Date de mise à jour :
    # - initialisée à now()
    # - mise à jour automatiquement lors d'un UPDATE
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
