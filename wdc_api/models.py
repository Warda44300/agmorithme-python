# app/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .database import Base

# Modèle SQLAlchemy pour la table "prospects".
class Prospect(Base):
    # Nom de la table dans la base de données
    __tablename__ = "prospects"

    # Définition des colonnes et de leur type
    id = Column(Integer, primary_key=True, index=True)            # ID auto-incrémenté
    name = Column(Text, nullable=True)                            # Nom du prospect
    title = Column(Text, nullable=True)                           # Poste ou titre
    sector = Column(Text, nullable=True)                          # Secteur d'activité
    url = Column(String, unique=True, nullable=False, index=True) # URL LinkedIn, clé unique
    email = Column(String, nullable=True)                         # Email (si disponible)
    phone = Column(String, nullable=True)                         # Téléphone (si disponible)
    address = Column(Text, nullable=True)                         # Adresse (si connue)
    city = Column(String, nullable=True)                          # Ville
    country = Column(String, nullable=True)                       # Pays
    source = Column(String, nullable=False, default="linkedin")   # Source des données (LinkedIn par défaut)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()                                 # Timestamp de création (défini par le serveur)
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),                                # Timestamp de mise à jour initialisé à now()
        onupdate=func.now()                                       # Mis à jour automatiquement lors d'une modification
    )