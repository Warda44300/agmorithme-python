"""
database.py
------------

Responsabilité :
- Centraliser la configuration de connexion à PostgreSQL
- Initialiser l'engine SQLAlchemy
- Fournir une session DB injectable dans FastAPI

Contexte :
- Driver PostgreSQL : psycopg v3 (compatible Python 3.13)
- ORM : SQLAlchemy 2.x
- Environnement : Windows / venv

Migration psycopg2 → psycopg3 :
- Détection et remplacement automatique dans l'URL
- Support des anciennes URLs pour rétrocompatibilité
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ✅ CHARGER LE FICHIER .env
load_dotenv()

# -------------------------------------------------------------------
# DATABASE_URL
# -------------------------------------------------------------------
# Priorité :
# 1) Variable d'environnement DATABASE_URL (recommandé en dev/prod)
# 2) Valeur par défaut locale (fallback)
#
# IMPORTANT :
# - Driver = psycopg (v3) → "postgresql+psycopg://"
# - psycopg2 NE DOIT PLUS être utilisé (version 2, obsolète)
# - Migration automatique si psycopg2 détecté dans l'URL
# -------------------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:Wardouse44300@127.0.0.1:5432/postgres"
)

# Migration automatique psycopg2 → psycopg3
# Permet de garder la compatibilité avec les anciennes configurations
if DATABASE_URL and "psycopg2" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("psycopg2", "psycopg")
    print(f"✅ Migration automatique: psycopg2 → psycopg3")
    print(f"   URL: {DATABASE_URL[:50]}...")

# -------------------------------------------------------------------
# ENGINE SQLALCHEMY
# -------------------------------------------------------------------
# pool_pre_ping=True :
# - Vérifie la validité des connexions avant utilisation
# - Évite les erreurs liées aux connexions mortes
# - Particulièrement utile avec PostgreSQL qui peut fermer les
#   connexions inactives après un certain temps
# -------------------------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# -------------------------------------------------------------------
# SESSION SQLALCHEMY
# -------------------------------------------------------------------
# SessionLocal :
# - Fournit une session par requête
# - Utilisée via dépendance FastAPI (Depends)
# - autocommit=False : transactions manuelles (recommandé)
# - autoflush=False : contrôle manuel du flush
# -------------------------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# -------------------------------------------------------------------
# BASE DECLARATIVE
# -------------------------------------------------------------------
# Base :
# - Classe mère de tous les modèles SQLAlchemy
# - Tous les modèles héritent de cette classe
# - Permet la génération automatique des tables via Base.metadata.create_all()
# -------------------------------------------------------------------

Base = declarative_base()

# -------------------------------------------------------------------
# DEPENDANCE FASTAPI : get_db
# -------------------------------------------------------------------
# Pattern de dépendance FastAPI :
# - Ouvre une session DB
# - La fournit aux routes via Depends(get_db)
# - Garantit la fermeture propre de la session (finally)
# - Permet la gestion automatique des transactions
#
# Usage dans les routes :
# @router.get("/")
# def read_data(db: Session = Depends(get_db)):
#     return db.query(Model).all()
# -------------------------------------------------------------------

def get_db():
    """
    Générateur de session SQLAlchemy pour FastAPI.
    
    Yields:
        Session: Session SQLAlchemy active
        
    Garanties:
        - La session est toujours fermée (finally)
        - Une session par requête HTTP
        - Isolation des transactions
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
