import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "bot.db")

DB_URL = f"sqlite:///{DB_PATH}"

# Создание каталога, если не существует
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def init_db():
    """Создаёт таблицы при запуске"""
    from .models import User, Order  # noqa
    Base.metadata.create_all(bind=engine)
