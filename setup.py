"""
Скрипт для настройки проекта.
"""

import os
import shutil
from pathlib import Path


def setup_project():
    """Настраивает проект для разработки."""
    print("🚀 Настройка проекта бота типографии...")
    
    # Создаем директории
    directories = [
        "uploads",
        "logs",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Создана директория: {directory}")
    
    # Копируем пример конфигурации
    if not Path(".env").exists():
        if Path("env.example").exists():
            shutil.copy("env.example", ".env")
            print("✅ Создан файл .env из примера")
        else:
            print("⚠️ Файл env.example не найден")
    
    # Создаем базу данных
    try:
        from init_db import init_database
        init_database()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
    
    print("\n🎉 Настройка завершена!")
    print("\n📋 Следующие шаги:")
    print("1. Отредактируйте файл .env с вашими настройками")
    print("2. Получите токен бота у @BotFather")
    print("3. Настройте OPERATOR_CHAT_ID и ADMIN_IDS")
    print("4. Запустите бота: python app.py")


if __name__ == "__main__":
    setup_project()
