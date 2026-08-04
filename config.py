import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "inminlu").strip().lstrip("@").lower()

CAFES = {
    "PUPU": {
        "emoji": "🔴",
        "phone": "8 914 556-00-22",
    },
    "Кофетюр": {
        "emoji": "🟢",
        "phone": "8 914 556-21-22",
    },
}

DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/zhuravushka_delivery.db").strip()
