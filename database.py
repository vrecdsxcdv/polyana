from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from config import config

engine = create_engine(config.DATABASE_URL, future=True, echo=False,
                       poolclass=StaticPool, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db(): return SessionLocal()

def safe_migrate():
    db = get_db()
    try:
        db.execute(text("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, tg_user_id INTEGER UNIQUE, username TEXT, first_name TEXT, last_name TEXT, created_at TEXT)"))
        db.execute(text("""
        CREATE TABLE IF NOT EXISTS orders (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          code TEXT UNIQUE, user_id INTEGER, what_to_print TEXT, quantity INTEGER,
          format TEXT, sides TEXT, paper TEXT, deadline_at TEXT, contact TEXT, notes TEXT,
          lamination TEXT DEFAULT 'none', bigovka_count INTEGER DEFAULT 0, corner_rounding INTEGER DEFAULT 0,
          sheet_format TEXT DEFAULT '', custom_size_mm TEXT DEFAULT '', material TEXT DEFAULT '',
          print_color TEXT DEFAULT 'color', status TEXT DEFAULT 'NEW', needs_operator INTEGER DEFAULT 0,
          created_at TEXT, updated_at TEXT
        )"""))
        db.execute(text("""
        CREATE TABLE IF NOT EXISTS attachments(
          id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, file_id TEXT, file_unique_id TEXT,
          original_name TEXT, mime_type TEXT, size INTEGER, tg_message_id INTEGER, from_chat_id INTEGER, kind TEXT, created_at TEXT
        )"""))
        # add columns if missed
        cols = {r[1] for r in db.execute(text("PRAGMA table_info(orders)"))}
        add = {
          "lamination":"TEXT DEFAULT 'none'","bigovka_count":"INTEGER DEFAULT 0","corner_rounding":"INTEGER DEFAULT 0",
          "sheet_format":"TEXT DEFAULT ''","custom_size_mm":"TEXT DEFAULT ''","material":"TEXT DEFAULT ''","print_color":"TEXT DEFAULT 'color'"
        }
        for name, ddl in add.items():
            if name not in cols:
                db.execute(text(f"ALTER TABLE orders ADD COLUMN {name} {ddl}"))
        db.commit()
    finally:
        db.close()

def create_tables():
    safe_migrate()