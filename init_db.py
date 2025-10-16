"""
Скрипт для инициализации базы данных.
"""

from __future__ import annotations

import logging
from db.session import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Инициализирует базу данных."""
    try:
        logger.info("Создание таблиц в базе данных...")
        init_db()
        logger.info("✅ База данных успешно инициализирована!")
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
        raise


if __name__ == "__main__":
    init_database()
