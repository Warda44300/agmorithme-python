# wdc_api/main.py
# ===============
# Point d'entrée FastAPI : crée l'app et branche les routes.

from fastapi import FastAPI

from wdc_api.routers.prospects import router as prospects_router

app = FastAPI(title="WDC Prospects API")

# Branche les routes /prospects
app.include_router(prospects_router)

