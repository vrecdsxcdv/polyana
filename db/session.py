import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_URL = os.getenv("SQLITE_URL") or "sqlite:////data/bot.db"  # Railway: /data — persistent
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def init_db():
    # импорт моделей перед create_all
    from .models import Order, User  # noqa: F401
    Base.metadata.create_all(bind=engine)
