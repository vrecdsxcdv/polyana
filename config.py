import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / '.env', override=True)

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN","")
    OPERATOR_CHAT_ID = os.getenv("OPERATOR_CHAT_ID","")
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip().isdigit()]
    TIMEZONE = os.getenv("TIMEZONE","Europe/Moscow")
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB","25"))
    DATABASE_URL = "sqlite:///bot.db"
config = Config()