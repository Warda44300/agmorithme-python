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
# - psycopg2 NE DOIT PLUS être utilisé
# -------------------------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:Wardouse44300@127.0.0.1:5432/postgres"
)

# -------------------------------------------------------------------
# ENGINE SQLALCHEMY
# -------------------------------------------------------------------
# pool_pre_ping=True :
# - Vérifie la validité des connexions avant utilisation
# - Évite les erreurs liées aux connexions mortes
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
# -------------------------------------------------------------------

Base = declarative_base()

# -------------------------------------------------------------------
# DEPENDANCE FASTAPI : get_db
# -------------------------------------------------------------------
# - Ouvre une session DB
# - La fournit aux routes
# - Garantit la fermeture propre de la session
# -------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
