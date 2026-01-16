"""
sync_prospects_postgres.py

But :
- Charger le fichier prospects_recommandes.csv
- Garder uniquement les prospects "recommended"
- Envoyer/mettre à jour les contacts dans PostgreSQL (table public.prospects)
- Clé unique = url  -> ON CONFLICT(url) DO UPDATE
"""

import psycopg2
from psycopg2.extras import execute_values
import pandas as pd

# -------------------------------------------------------------------
# 0) Config
# -------------------------------------------------------------------

# Chemin du fichier généré par tri_linkedin_plus.py
CSV_PATH = "prospects_recommandes.csv"

# Paramètres de connexion PostgreSQL
# ⚠️ Si tu changes ton mot de passe ou le nom de la base,
#    pense à les mettre à jour ici.
PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "wdc_prospects",
    "user": "postgres",
    "password": "Wardouse44300@",  # adapte si besoin
}


# -------------------------------------------------------------------
# 1) Connexion PostgreSQL
# -------------------------------------------------------------------

def get_connection():
    """Crée une connexion PostgreSQL."""
    return psycopg2.connect(**PG_CONFIG)


# -------------------------------------------------------------------
# 2) Charger et filtrer le CSV
# -------------------------------------------------------------------

def load_prospects(csv_path: str) -> pd.DataFrame:
    print("📄 Chargement du CSV :", csv_path)

    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # Normalisation des noms de colonnes (tout en minuscules)
    df.columns = [c.strip().lower() for c in df.columns]

    # Affichage des colonnes pour debug
    print("Colonnes trouvées dans le CSV :", list(df.columns))

    # --- Filtre sur "recommended" si la colonne existe ---
    if "recommended" in df.columns:
        print("\nValeurs trouvées dans 'recommended' :")
        print(df["recommended"].value_counts())

        col = df["recommended"].astype(str).str.lower().str.strip()
        mask_reco = col.isin(["true", "1", "yes", "oui"])

        df = df[mask_reco].copy()
        print(f"\n✅ Prospects recommandés conservés : {len(df)} lignes")
    else:
        print("⚠️ Pas de colonne 'recommended' dans le CSV (aucun filtrage appliqué)")

    # --- Nettoyage minimal de l'URL (clé unique) ---
    if "url" not in df.columns:
        raise ValueError("La colonne 'url' est obligatoire pour la clé unique dans PostgreSQL.")

    df["url"] = df["url"].astype(str).str.strip()
    df = df[df["url"] != ""].copy()

    # On enlève les vrais doublons d'URL côté CSV pour éviter de pousser
    # 10 fois la même ligne dans la même exécution.
    df = df.drop_duplicates(subset=["url"], keep="first")

    print(f"📌 Lignes restantes après nettoyage / dédoublonnage : {len(df)}")

    # Petit aperçu pour contrôle visuel
    print("\nAperçu des 5 premières lignes :")
    print(df[["name", "title", "sector", "url"]].head())

    return df


# -------------------------------------------------------------------
# 3) Insertion / mise à jour dans PostgreSQL
# -------------------------------------------------------------------

def insert_prospects(df: pd.DataFrame) -> None:
    """Insère ou met à jour les prospects dans la table public.prospects.

    Schéma attendu (côté PostgreSQL) :
        id SERIAL PRIMARY KEY,
        name      TEXT,
        title     TEXT,
        sector    TEXT,
        url       TEXT UNIQUE,
        email     TEXT,
        phone     TEXT,
        address   TEXT,
        city      TEXT,
        country   TEXT,
        source    TEXT DEFAULT 'linkedin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    """

    if df.empty:
        print("⚠️ Aucun prospect à envoyer. Vérifie le CSV / les filtres.")
        return

    print(f"\n➡️ Envoi de {len(df)} lignes vers PostgreSQL...")

    conn = get_connection()
    cur = conn.cursor()

    # Requête UPSERT : insert ou update si l'URL existe déjà
    upsert_sql = """
        INSERT INTO public.prospects (
            name, title, sector, url,
            email, phone, address, city, country
        )
        VALUES %s
        ON CONFLICT (url)
        DO UPDATE SET
            name    = EXCLUDED.name,
            title   = EXCLUDED.title,
            sector  = EXCLUDED.sector,
            email   = EXCLUDED.email,
            phone   = EXCLUDED.phone,
            address = EXCLUDED.address,
            city    = EXCLUDED.city,
            country = EXCLUDED.country,
            updated_at = NOW();
    """

    # Préparation des données au format attendu par execute_values
    rows = []
    for _, row in df.iterrows():
        rows.append((
            row.get("name"),
            row.get("title"),
            row.get("sector"),
            row.get("url"),
            row.get("email"),
            row.get("phone"),
            row.get("address"),
            row.get("city"),
            row.get("country"),
        ))

    # Insertion en bulk
    execute_values(cur, upsert_sql, rows)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Sync PostgreSQL terminée !")


# -------------------------------------------------------------------
# 4) Programme principal
# -------------------------------------------------------------------

if __name__ == "__main__":
    prospects = load_prospects(CSV_PATH)
    insert_prospects(prospects)