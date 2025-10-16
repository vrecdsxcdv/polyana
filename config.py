import os

def _parse_admin_ids(val: str) -> set[int]:
    if not val:
        return set()
    parts = [p.strip() for p in val.split(",")]
    out: set[int] = set()
    for p in parts:
        if not p:
            continue
        try:
            out.add(int(p))
        except ValueError:
            pass
    return out
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / '.env', override=True)

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN","")
    OPERATOR_CHAT_ID = int(os.getenv("OPERATOR_CHAT_ID","0")) if os.getenv("OPERATOR_CHAT_ID","").strip() else 0
    ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    OPERATORS = [int(x) for x in os.getenv("OPERATORS","").split(",") if x.strip().lstrip('-').isdigit()]
    TIMEZONE = os.getenv("TIMEZONE","Europe/Moscow")
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB","25"))
    DATABASE_URL = "sqlite:///bot.db"
config = Config()