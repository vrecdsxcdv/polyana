import random
import string
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from typing import List, Tuple
from sqlalchemy import func
from sqlalchemy import select
from database import get_db, Base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from models import OrderDTO

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    what_to_print = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0)
    format = Column(String(50), default="")
    sides = Column(String(10), default="")
    paper = Column(String(50), default="")
    deadline_at = Column(DateTime, nullable=True)
    contact = Column(String(50), default="")
    notes = Column(Text, default="")
    lamination = Column(String(20), default="none")
    bigovka_count = Column(Integer, default=0)
    corner_rounding = Column(Boolean, default=False)
    sheet_format = Column(String(20), default="")
    custom_size_mm = Column(String(50), default="")
    material = Column(String(20), default="")
    print_color = Column(String(10), default="color")
    status = Column(String(20), default="NEW")
    needs_operator = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Пользовательские статусы для отображения
STATUS_MAP = {
    "NEW": "Новый",
    "TAKEN": "Взято",
    "IN_PROGRESS": "В работе",
    "DONE": "Готово",
    "COMPLETED": "Готов",  # совместимость со старыми хендлерами
    "READY": "Готов",       # совместимость из README
}

def generate_order_code() -> str:
    """Генерирует уникальный код заказа в формате XXXXXX-XXXX"""
    while True:
        # Генерируем 6 цифр + 4 цифры
        part1 = ''.join(random.choices(string.digits, k=6))
        part2 = ''.join(random.choices(string.digits, k=4))
        code = f"{part1}-{part2}"
        
        # Проверяем уникальность
        db = get_db()
        try:
            existing = db.query(Order).filter(Order.code == code).first()
            if not existing:
                return code
        finally:
            db.close()

def create_order(user_data: dict, user_id: int) -> Order:
    """Создает новый заказ в базе данных"""
    db = get_db()
    try:
        order = Order(
            code=generate_order_code(),
            user_id=user_id,
            what_to_print=user_data.get('what_to_print', ''),
            quantity=user_data.get('quantity', 0),
            format=user_data.get('format', ''),
            sides=user_data.get('sides', ''),
            paper=user_data.get('paper', ''),
            deadline_at=user_data.get('deadline_at'),
            contact=user_data.get('contact', ''),
            notes=user_data.get('notes', ''),
            lamination=user_data.get('lamination', 'none'),
            bigovka_count=user_data.get('bigovka_count', 0),
            corner_rounding=user_data.get('corner_rounding', False),
            sheet_format=user_data.get('sheet_format', ''),
            custom_size_mm=user_data.get('custom_size_mm', ''),
            material=user_data.get('material', ''),
            print_color=user_data.get('print_color', 'color'),
            status='NEW',
            needs_operator=False
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    finally:
        db.close()

def update_order_status(order_id: int, status: str, operator_username: str = None) -> bool:
    """Обновляет статус заказа"""
    db = get_db()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            order.updated_at = datetime.utcnow()
            if operator_username:
                order.notes = f"{order.notes}\n\nОператор: @{operator_username}".strip()
            db.commit()
            return True
        return False
    finally:
        db.close()

def get_order_by_code_session(session, code: str):
    """
    Безопасно вернуть заказ по коду (строка вида YYMMDD-XXXX) или None.
    Принимает готовую сессию, чтобы вызывать в рамках одного запроса.
    """
    try:
        return session.query(Order).filter(Order.code == code).one()
    except NoResultFound:
        return None
    except Exception:
        return None

def get_order_by_code(code: str):
    """
    Обертка: получить заказ по коду, открывает/закрывает сессию внутри.
    Совместима с хендлерами, где нет явной сессии.
    """
    db = get_db()
    try:
        return db.query(Order).filter(Order.code == code).first()
    finally:
        db.close()

def get_user_orders(user_id: int, limit: int = 10) -> list[Order]:
    """Получает заказы пользователя"""
    db = get_db()
    try:
        return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(limit).all()
    finally:
        db.close()

# ---- Admin helpers ----
STATUS_DONE_KEYS = {"DONE", "COMPLETED", "READY", "готов", "готово", "выполнен", "finished"}

def list_active_orders(offset: int = 0, limit: int = 10) -> Tuple[List[Order], int]:
    """
    Возвращает (orders, total_count) — все заказы, у которых статус не "готов/выполнен".
    """
    db = get_db()
    try:
        base_query = db.query(Order).filter(~Order.status.in_(STATUS_DONE_KEYS))
        total = db.query(func.count()).select_from(base_query.subquery()).scalar() or 0
        orders = base_query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
        return orders, int(total)
    finally:
        db.close()

def ensure_order_code(order) -> str:
    """Если у заказа нет кода — генерируем и сохраняем."""
    if not getattr(order, "code", None):
        import uuid
        code = str(uuid.uuid4())[:8].upper()
        order.code = code
        db = get_db()
        try:
            merged = db.merge(order)
            db.commit()
        finally:
            db.close()
        return code
    return order.code

# Заглушки для админ-панели
async def list_orders_admin(offset: int, limit: int, exclude_statuses=None):
    """Заглушка для админ-панели - адаптируй под свою ORM/модель."""
    exclude_statuses = exclude_statuses or []
    # верни list[dict]: id, code, category_title, quantity, status
    # ... SELECT ... WHERE status NOT IN (...)
    return []

async def get_order_admin(order_id: int):
    """Заглушка для админ-панели - верни dict для карточки."""
    return None

def format_order_for_user(order) -> str:
    """
    Краткая читаемая карточка для пользователя.
    Не менять существующие карточки в операторский чат!
    """
    status = STATUS_MAP.get(order.status or "NEW", order.status or "NEW")
    lines = [
        f"🧾 Заказ #{order.code}",
        f"Статус: {status}",
    ]
    if getattr(order, "product_human", None):
        lines.append(f"Тип: {order.product_human}")
    if getattr(order, "what_to_print", None) and not getattr(order, "product_human", None):
        lines.append(f"Тип: {order.what_to_print}")
    if getattr(order, "quantity", None):
        lines.append(f"Тираж/кол-во: {order.quantity}")
    if getattr(order, "sheet_format", None):
        lines.append(f"Формат: {order.sheet_format}")
    if getattr(order, "print_color", None):
        lines.append(f"Печать: {order.print_color}")
    # срок, если сохранён
    due = getattr(order, "deadline_at", None)
    if due:
        if isinstance(due, datetime):
            lines.append(f"Срок: {due.strftime('%d.%m.%Y %H:%M')}")
        else:
            lines.append(f"Срок: {due}")
    else:
        lines.append("Срок: менеджер уточнит после проверки макета.")
    return "\n".join(lines)