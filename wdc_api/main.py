"""
wdc_api/main.py
===============

Objectif :
- Créer l'application FastAPI
- Inclure les routers (ex: prospects)
- Forcer la déclaration OpenAPI d'une auth API Key pour afficher "Authorize" dans Swagger

Pourquoi forcer OpenAPI ?
- Parfois, selon la façon dont les dépendances sont branchées, FastAPI ne génère pas
  automatiquement "securitySchemes". Résultat : pas de bouton Authorize.
- Ici on ajoute explicitement un schéma API Key (X-API-Key) dans OpenAPI.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from wdc_api.routers import prospects


app = FastAPI(
    title="WDC Prospects API",
    version="0.1.0",
)


# ---------------------------------------------------------------------
# OpenAPI custom : ajout explicite du schéma de sécurité "ApiKeyAuth"
# ---------------------------------------------------------------------
def custom_openapi():
    # Si déjà généré, on le renvoie (cache)
    if app.openapi_schema:
        return app.openapi_schema

    # Génération standard
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description="API de gestion de prospects (protégée par clé API).",
    )

    # Ajout du schéma API Key dans components.securitySchemes
    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})

    security_schemes["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Clé API à fournir dans le header X-API-Key",
    }

    # Option 1 (simple et efficace) : afficher Authorize globalement
    # => Swagger montrera le bouton Authorize même si aucune route n'a Security(...)
    openapi_schema["security"] = [{"ApiKeyAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# On remplace la génération OpenAPI par la nôtre
app.openapi = custom_openapi  # type: ignore


# ---------------------------------------------------------------------
# Include routers
# ---------------------------------------------------------------------
app.include_router(prospects.router)

