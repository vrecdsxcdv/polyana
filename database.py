"""
Настройка базы данных и SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from config import config

# Создаем движок базы данных
engine = create_engine(
    config.DATABASE_URL,
    future=True,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


def get_db():
    """Получить сессию базы данных."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Сессия будет закрыта в finally блоке вызывающего кода


def safe_migrate():
    """Безопасная миграция для добавления новых полей."""
    db = get_db()
    try:
        # Получаем информацию о существующих колонках
        from sqlalchemy import text
        existing = {row[1] for row in db.execute(text("PRAGMA table_info(orders);"))}
        
        # Новые колонки для добавления
        new_cols = {
            "lamination": "TEXT DEFAULT 'none'",
            "bigovka_count": "INTEGER DEFAULT 0", 
            "corner_rounding": "INTEGER DEFAULT 0",
            "sheet_format": "TEXT DEFAULT ''",
            "custom_size_mm": "TEXT DEFAULT ''",
            "material": "TEXT DEFAULT ''",
            "print_color": "TEXT DEFAULT 'color'",
        }
        
        # Добавляем только отсутствующие колонки
        for name, ddl in new_cols.items():
            if name not in existing:
                try:
                    db.execute(text(f"ALTER TABLE orders ADD COLUMN {name} {ddl}"))
                    print(f"✅ Добавлена колонка: {name}")
                except Exception as col_error:
                    print(f"⚠️ Ошибка добавления колонки {name}: {col_error}")
        
        db.commit()
        print("✅ Миграция базы данных завершена")
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """Создать все таблицы в базе данных."""
    try:
        # Импортируем все модели для создания таблиц
        from models import User, Order, Attachment
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы базы данных созданы/проверены")
        
        # Выполняем безопасную миграцию
        try:
            safe_migrate()
        except Exception as migrate_error:
            print(f"⚠️ Предупреждение: ошибка при миграции: {migrate_error}")
            
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        raise