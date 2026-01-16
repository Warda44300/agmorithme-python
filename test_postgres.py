import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="wdc_prospects",
        user="postgres",
        password="Wardouse44300"
    )

    print("✅ Connexion PostgreSQL OK !")
    conn.close()

except Exception as e:
    print("❌ Erreur :", e)
