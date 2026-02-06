"""
tools/linkedin_login.py
=======================

Objectif :
- Ouvrir un navigateur Chromium non-headless (visible)
- Te laisser te connecter manuellement à LinkedIn
- Sauvegarder la session (cookies, local storage, etc.) dans storage/linkedin_state.json

Usage :
    python tools/linkedin_login.py

Notes :
- Le navigateur reste ouvert 60 secondes pour que tu aies le temps de te connecter
- Une fois connecté, la session est automatiquement sauvegardée
- Le fichier storage/linkedin_state.json est ignoré par Git (.gitignore)
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


# Chemin absolu vers le dossier storage/
STORAGE_DIR = Path(__file__).parent.parent / "storage"
STORAGE_DIR.mkdir(exist_ok=True)  # Créer storage/ si n'existe pas

# Fichier de session LinkedIn
SESSION_FILE = STORAGE_DIR / "linkedin_state.json"


async def main():
    print("🚀 Ouverture du navigateur pour connexion LinkedIn...")
    print(f"📁 Session sera sauvegardée dans : {SESSION_FILE}")
    
    async with async_playwright() as p:
        # Lancer Chromium en mode visible (headless=False)
        browser = await p.chromium.launch(
            headless=False,  # Navigateur visible
            slow_mo=50,      # Ralentir légèrement les actions (optionnel)
        )
        
        # Créer un contexte de navigation (isolé)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        
        # Ouvrir une nouvelle page
        page = await context.new_page()
        
        # Aller sur LinkedIn
        print("🔗 Navigation vers LinkedIn...")
        await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        
        print("\n" + "="*60)
        print("⏳ CONNECTE-TOI MANUELLEMENT À LINKEDIN")
        print("="*60)
        print("1. Entre ton email/mot de passe")
        print("2. Valide la connexion (+ 2FA si nécessaire)")
        print("3. Attends d'arriver sur le feed LinkedIn")
        print("4. Le script va sauvegarder la session automatiquement")
        print("="*60 + "\n")
        
        # Attendre 60 secondes pour laisser le temps de se connecter
        # (tu peux augmenter si tu as besoin de plus de temps)
        await asyncio.sleep(60)
        
        # Sauvegarder la session (cookies + local storage + etc.)
        print("💾 Sauvegarde de la session...")
        await context.storage_state(path=str(SESSION_FILE))
        
        print(f"✅ Session sauvegardée dans : {SESSION_FILE}")
        print("🔒 Ce fichier est ignoré par Git (sécurité)")
        
        # Fermer le navigateur
        await browser.close()
        
    print("\n✅ Terminé ! Tu peux maintenant utiliser linkedin_test_session.py")


if __name__ == "__main__":
    asyncio.run(main())