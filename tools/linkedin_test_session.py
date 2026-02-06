"""
tools/linkedin_test_session.py
==============================

Objectif :
- Ouvrir un navigateur en utilisant la session sauvegardée (storage/linkedin_state.json)
- Vérifier qu'on accède au feed LinkedIn sans avoir à se reconnecter
- Prouver que la session est valide et réutilisable

Usage :
    python tools/linkedin_test_session.py

Prérequis :
- Avoir lancé linkedin_login.py au moins une fois pour créer storage/linkedin_state.json
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


# Chemin vers le fichier de session
STORAGE_DIR = Path(__file__).parent.parent / "storage"
SESSION_FILE = STORAGE_DIR / "linkedin_state.json"


async def main():
    # Vérifier que le fichier de session existe
    if not SESSION_FILE.exists():
        print("❌ Erreur : Fichier de session introuvable !")
        print(f"📁 Attendu : {SESSION_FILE}")
        print("\n💡 Solution : Lance d'abord 'python tools/linkedin_login.py'")
        return
    
    print("🚀 Test de la session LinkedIn sauvegardée...")
    print(f"📁 Chargement de : {SESSION_FILE}")
    
    async with async_playwright() as p:
        # Lancer Chromium en mode visible
        browser = await p.chromium.launch(
            headless=False,  # Visible pour voir le résultat
            slow_mo=50,
        )
        
        # Créer un contexte EN CHARGEANT LA SESSION SAUVEGARDÉE
        context = await browser.new_context(
            storage_state=str(SESSION_FILE),  # ← Magie : on charge la session !
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        
        # Ouvrir une page
        page = await context.new_page()
        
        # Aller directement sur le feed LinkedIn
        print("🔗 Navigation vers le feed LinkedIn...")
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        
        # Attendre un peu pour laisser la page charger
        await asyncio.sleep(3)
        
        # Vérifier qu'on est bien connecté (pas redirigé vers /login)
        current_url = page.url
        print(f"\n📍 URL actuelle : {current_url}")
        
        if "login" in current_url.lower():
            print("❌ ÉCHEC : Session expirée ou invalide (redirigé vers login)")
            print("💡 Solution : Relance 'python tools/linkedin_login.py' pour te reconnecter")
        else:
            print("✅ SUCCÈS : Session valide ! Tu es connecté à LinkedIn")
            print("🎉 Le navigateur va rester ouvert 10 secondes pour que tu vérifies")
            
            # Garder le navigateur ouvert 10 secondes
            await asyncio.sleep(10)
        
        # Fermer
        await browser.close()
        
    print("\n✅ Test terminé !")


if __name__ == "__main__":
    asyncio.run(main())