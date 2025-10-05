"""
Конфигурация бота типографии.
"""

import os
from typing import List, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class Config:
    """Конфигурация приложения."""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    # Проверка токена будет в main() функции
    
    # Operator Chat
    OPERATOR_CHAT_ID: Optional[str] = os.getenv("OPERATOR_CHAT_ID")
    
    # Admin Configuration
    ADMIN_IDS: List[int] = []
    if admin_ids_str := os.getenv("ADMIN_IDS"):
        try:
            ADMIN_IDS = [int(admin_id.strip()) for admin_id in admin_ids_str.split(",")]
        except ValueError:
            print("Предупреждение: неверный формат ADMIN_IDS")
    
    # File Upload and time/pricing
    TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Moscow")
    BW_PRICE_PER_SHEET: float = float(os.getenv("BW_PRICE_PER_SHEET", "5.0"))
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    MAX_UPLOAD_BYTES: int = MAX_UPLOAD_MB * 1024 * 1024
    
    # Database
    DATABASE_URL: str = "sqlite:///bot.db"
    
    # Uploads directory
    UPLOADS_DIR: str = "uploads"
    
    # Allowed file types for layouts
    ALLOWED_EXTENSIONS: set[str] = {".pdf",".ai",".eps",".psd",".tif",".tiff",".jpg",".jpeg",".png",".cdr",".svg",".zip"}
    ALLOWED_MIME_TYPES: set[str] = {
        "application/pdf",
        "application/postscript",
        "image/jpeg",
        "image/png",
        "application/zip",
        "application/x-zip-compressed"
    }


# Глобальный экземпляр конфигурации
config = Config()