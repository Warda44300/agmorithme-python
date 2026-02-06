import os
from sqlalchemy import text
from wdc_api.database import engine

print("WDC_API_KEY =", os.getenv("WDC_API_KEY"))

with engine.begin() as c:
    c.execute(
        text(
            "INSERT INTO prospects (url, source) "
            "VALUES ('https://linkedin.com/in/test', 'linkedin') "
            "ON CONFLICT (url) DO NOTHING"
        )
    )

    r = c.execute(text("SELECT count(*) FROM prospects"))
    print("prospects_count =", r.scalar())
