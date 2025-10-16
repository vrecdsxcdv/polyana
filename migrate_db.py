#!/usr/bin/env python3
"""
Скрипт миграции базы данных для добавления недостающих колонок.
"""

import logging
from sqlalchemy import text
from db.session import engine, SessionLocal

def get_db(): return SessionLocal()

logger = logging.getLogger(__name__)

def migrate_database():
    """Выполняет миграцию базы данных."""
    db = None
    try:
        db = get_db()
        
        # Список миграций для выполнения
        migrations = [
            # Добавляем колонку size_bytes в attachments если её нет
            {
                "name": "add_size_bytes_to_attachments",
                "sql": "ALTER TABLE attachments ADD COLUMN size_bytes INTEGER",
                "check": "SELECT COUNT(*) FROM pragma_table_info('attachments') WHERE name='size_bytes'"
            },
            # Добавляем колонку size в attachments если её нет
            {
                "name": "add_size_to_attachments", 
                "sql": "ALTER TABLE attachments ADD COLUMN size INTEGER",
                "check": "SELECT COUNT(*) FROM pragma_table_info('attachments') WHERE name='size'"
            },
            # Добавляем колонку status в orders если её нет
            {
                "name": "add_status_to_orders",
                "sql": "ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'NEW'",
                "check": "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='status'"
            },
            # Новые поля для постобработки и форматов
            {
                "name": "add_lamination_to_orders",
                "sql": "ALTER TABLE orders ADD COLUMN lamination TEXT DEFAULT 'none'",
                "check": "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='lamination'"
            },
            {
                "name": "add_bigovka_count_to_orders",
                "sql": "ALTER TABLE orders ADD COLUMN bigovka_count INTEGER DEFAULT 0",
                "check": "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='bigovka_count'"
            },
            {
                "name": "add_corner_rounding_to_orders",
                "sql": "ALTER TABLE orders ADD COLUMN corner_rounding BOOLEAN DEFAULT 0",
                "check": "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='corner_rounding'"
            },
            {
                "name": "add_sheet_format_to_orders",
                "sql": "ALTER TABLE orders ADD COLUMN sheet_format TEXT DEFAULT ''",
                "check": "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='sheet_format'"
            },
            {
                "name": "add_custom_size_mm_to_orders",
                "sql": "ALTER TABLE orders ADD COLUMN custom_size_mm TEXT DEFAULT ''",
                "check": "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='custom_size_mm'"
            },
            {
                "name": "add_sheets_qty_to_orders",
                "sql": "ALTER TABLE orders ADD COLUMN sheets_qty INTEGER",
                "check": "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='sheets_qty'"
            },
            {
                "name": "add_calc_sum_to_orders",
                "sql": "ALTER TABLE orders ADD COLUMN calc_sum REAL",
                "check": "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='calc_sum'"
            }
            ,{
                "name": "add_material_to_orders",
                "sql": "ALTER TABLE orders ADD COLUMN material TEXT DEFAULT ''",
                "check": "SELECT COUNT(*) FROM pragma_table_info('orders') WHERE name='material'"
            }
        ]
        
        for migration in migrations:
            try:
                # Проверяем, существует ли колонка
                result = db.execute(text(migration["check"])).fetchone()
                if result[0] == 0:
                    logger.info(f"Выполняем миграцию: {migration['name']}")
                    db.execute(text(migration["sql"]))
                    db.commit()
                    logger.info(f"✅ Миграция {migration['name']} выполнена успешно")
                else:
                    logger.info(f"⏭️ Колонка уже существует, пропускаем: {migration['name']}")
            except Exception as e:
                logger.error(f"❌ Ошибка при выполнении миграции {migration['name']}: {e}")
                db.rollback()
        
        logger.info("🎉 Все миграции выполнены!")
        
    except Exception as e:
        logger.exception(f"Критическая ошибка при миграции: {e}")
        if db:
            db.rollback()
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_database()
