"""
Сервис для работы с заказами.
"""

from models import Order
from database import get_db
from texts import STATUS_TITLES


def get_user_orders(user_id, limit=10, offset=0):
    """Получает список заказов пользователя."""
    db = get_db()
    try:
        q = (db.query(Order)
               .filter(Order.user_id == user_id)
               .order_by(Order.created_at.desc()))
        total = q.count()
        rows = q.offset(offset).limit(limit).all()
        items = []
        for o in rows:
            # короткое название для кнопки, например "№{o.code} • {o.what_to_print}"
            short = f"№{o.code} • {o.what_to_print}"
            status = STATUS_TITLES.get(o.status.value, o.status.value)
            items.append((o.id, short, status))
        has_more = total > offset + len(rows)
        return items, has_more
    finally:
        db.close()


def get_order_by_id(order_id):
    """Получает заказ по ID."""
    db = get_db()
    try:
        return db.query(Order).get(order_id)
    finally:
        db.close()
