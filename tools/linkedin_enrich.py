"""
tools/linkedin_enrich.py
========================

Objectif :
- Lire un CSV minimal (first_name, last_name, linkedin_url)
- Pour chaque profil LinkedIn, extraire : headline, company, location
- Insérer ou mettre à jour les données dans la table prospects (PostgreSQL)

Usage :
    python tools/linkedin_enrich.py prospects_minimal.csv

Prérequis :
- Session LinkedIn valide (storage/linkedin_state.json)
- Base de données PostgreSQL accessible
- Variable d'environnement DATABASE_URL configurée (ou définie dans .env)

Notes :
- Le script utilise Playwright avec la session sauvegardée
- Délai de 2-4 secondes entre chaque profil (human-like behavior)
- Affiche une barre de progression en temps réel
"""

import asyncio
import csv
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page
import random
from dotenv import load_dotenv

# Ajouter le dossier parent au PYTHONPATH pour importer wdc_api
sys.path.insert(0, str(Path(__file__).parent.parent))

# ✅ CORRECTION : CHARGER LE FICHIER .env DEPUIS LA RACINE DU PROJET
BASE_DIR = Path(__file__).parent.parent
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path)

print(f"🔧 Chargement du .env depuis : {dotenv_path}")
print(f"🔧 Fichier .env existe : {dotenv_path.exists()}")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from wdc_api.models import Prospect
from wdc_api.database import Base


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

# Chemin vers le fichier de session LinkedIn
STORAGE_DIR = Path(__file__).parent.parent / "storage"
SESSION_FILE = STORAGE_DIR / "linkedin_state.json"

# ✅ CORRECTION : Récupérer DATABASE_URL depuis .env (chargé par load_dotenv)
DATABASE_URL = os.getenv("DATABASE_URL")

# Vérification de sécurité
if not DATABASE_URL:
    print("❌ ERREUR : DATABASE_URL non trouvé dans le fichier .env")
    print("💡 Solution : Vérifiez que le fichier .env contient : DATABASE_URL=postgresql+psycopg://...")
    sys.exit(1)

# Afficher l'URL (masquée) pour debug
masked_url = DATABASE_URL.replace(DATABASE_URL.split('@')[0].split(':')[-1], '***')
print(f"🔗 DATABASE_URL chargé : {masked_url}\n")

# Délais entre chaque profil (en secondes) - aléatoire pour paraître humain
MIN_DELAY = 2
MAX_DELAY = 4


# ---------------------------------------------------------------------
# Fonctions d'extraction LinkedIn
# ---------------------------------------------------------------------

async def extract_profile_data(page: Page, url: str) -> Optional[Dict[str, str]]:
    """
    Extrait les données d'un profil LinkedIn.
    
    Retourne un dict avec :
    - title (headline)
    - company (nom de l'entreprise actuelle)
    - location (ville, pays)
    
    Retourne None si échec (profil privé, erreur, etc.)
    """
    try:
        # Naviguer vers le profil
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        
        # Attendre que le contenu principal soit chargé
        # Sélecteur du titre (headline) - peut varier selon le type de profil
        await page.wait_for_selector("h1", timeout=5000)
        
        # Extraire le titre (headline)
        title = None
        try:
            # Le headline est généralement dans un div avec classe contenant "headline"
            title_elem = await page.query_selector('div[class*="headline"]')
            if title_elem:
                title = await title_elem.inner_text()
                title = title.strip()
        except:
            pass
        
        # Si pas trouvé avec la méthode précédente, essayer une autre
        if not title:
            try:
                title_elem = await page.query_selector('div.text-body-medium')
                if title_elem:
                    title = await title_elem.inner_text()
                    title = title.strip()
            except:
                pass
        
        # Extraire l'entreprise actuelle (company)
        company = None
        try:
            # Chercher dans la section "Expérience" ou dans le sous-titre du profil
            company_elem = await page.query_selector('div[class*="experience"] li:first-child h3')
            if company_elem:
                company = await company_elem.inner_text()
                company = company.strip()
        except:
            pass
        
        # Extraire la localisation
        location = None
        try:
            location_elem = await page.query_selector('span.text-body-small.inline.t-black--light.break-words')
            if location_elem:
                location = await location_elem.inner_text()
                location = location.strip()
        except:
            pass
        
        # Résultat
        result = {
            "title": title,
            "company": company,
            "location": location,
        }
        
        print(f"  ✅ Extrait : {result}")
        return result
        
    except Exception as e:
        print(f"  ❌ Erreur lors de l'extraction : {e}")
        return None


# ---------------------------------------------------------------------
# Fonctions DB
# ---------------------------------------------------------------------

def setup_database():
    """Créer l'engine et la session SQLAlchemy."""
    engine = create_engine(DATABASE_URL, echo=False)
    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def upsert_prospect(db_session, linkedin_url: str, first_name: str, last_name: str, data: Dict[str, str]):
    """
    Insère ou met à jour un prospect dans la DB.
    
    - Si l'URL existe déjà → UPDATE
    - Sinon → INSERT
    """
    # Chercher si le prospect existe déjà
    existing = db_session.query(Prospect).filter(Prospect.url == linkedin_url).first()
    
    # Construire le nom complet
    full_name = f"{first_name} {last_name}".strip()
    
    # Séparer location en city/country (basique)
    city = None
    country = None
    if data.get("location"):
        parts = data["location"].split(",")
        if len(parts) == 2:
            city = parts[0].strip()
            country = parts[1].strip()
        elif len(parts) == 1:
            city = parts[0].strip()
    
    if existing:
        # UPDATE
        print(f"  🔄 Mise à jour du prospect existant (ID {existing.id})")
        existing.name = full_name
        existing.title = data.get("title") or existing.title
        existing.sector = data.get("company") or existing.sector
        existing.city = city or existing.city
        existing.country = country or existing.country
        db_session.commit()
    else:
        # INSERT
        print(f"  ➕ Création d'un nouveau prospect")
        new_prospect = Prospect(
            url=linkedin_url,
            name=full_name,
            title=data.get("title"),
            sector=data.get("company"),
            city=city,
            country=country,
            source="linkedin"
        )
        db_session.add(new_prospect)
        db_session.commit()


# ---------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------

async def main(csv_path: str):
    """
    Fonction principale : lit le CSV, enrichit via LinkedIn, met à jour la DB.
    """
    # Vérifier que le fichier CSV existe
    csv_file = Path(csv_path)
    if not csv_file.exists():
        print(f"❌ Erreur : Fichier CSV introuvable : {csv_path}")
        return
    
    # Vérifier que la session LinkedIn existe
    if not SESSION_FILE.exists():
        print(f"❌ Erreur : Session LinkedIn introuvable : {SESSION_FILE}")
        print("💡 Solution : Lance d'abord 'python tools/linkedin_login.py'")
        return
    
    # Lire le CSV
    print(f"📁 Lecture du CSV : {csv_path}")
    prospects = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prospects.append(row)
    
    print(f"✅ {len(prospects)} prospects trouvés dans le CSV\n")
    
    # Setup DB
    print("🗄️ Connexion à la base de données...")
    db_session = setup_database()
    print("✅ Connexion DB OK\n")
    
    # Setup Playwright
    print("🚀 Démarrage de Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Visible pour debug (mettre True en prod)
            slow_mo=50,
        )
        
        context = await browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        
        page = await context.new_page()
        
        print("✅ Navigateur prêt\n")
        print("=" * 70)
        print("ENRICHISSEMENT EN COURS")
        print("=" * 70 + "\n")
        
        # Boucle sur chaque prospect
        for i, row in enumerate(prospects, start=1):
            first_name = row.get("first_name", "")
            last_name = row.get("last_name", "")
            linkedin_url = row.get("linkedin_url", "")
            
            if not linkedin_url:
                print(f"[{i}/{len(prospects)}] ⚠️ Pas d'URL LinkedIn pour {first_name} {last_name}, ignoré")
                continue
            
            print(f"[{i}/{len(prospects)}] 🔍 Enrichissement : {first_name} {last_name}")
            print(f"  🔗 URL : {linkedin_url}")
            
            # Extraire les données du profil
            data = await extract_profile_data(page, linkedin_url)
            
            if data:
                # Mettre à jour la DB
                upsert_prospect(db_session, linkedin_url, first_name, last_name, data)
            else:
                print(f"  ⚠️ Échec de l'extraction, profil ignoré")
            
            # Délai aléatoire entre chaque profil (human-like)
            if i < len(prospects):
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"  ⏳ Attente {delay:.1f}s avant le prochain profil...\n")
                await asyncio.sleep(delay)
        
        # Fermer le navigateur
        await browser.close()
    
    # Fermer la session DB
    db_session.close()
    
    print("\n" + "=" * 70)
    print("✅ ENRICHISSEMENT TERMINÉ")
    print("=" * 70)
    print(f"📊 {len(prospects)} prospects traités")
    print(f"🗄️ Données sauvegardées dans PostgreSQL")


# ---------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage : python tools/linkedin_enrich.py <fichier.csv>")
        print("Exemple : python tools/linkedin_enrich.py prospects_minimal.csv")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    asyncio.run(main(csv_path))