"""
Вспомогательные функции и константы для callback_data операторов.
"""

# Константы действий оператора
OP_TAKE = "op:TAKE"           # Принять в работу
OP_READY = "op:READY"         # Готово
OP_NEEDS_FIX = "op:NEEDS"     # Нужны правки
OP_CONTACT = "op:CONTACT"     # Связаться с клиентом


def make_cb(action: str, order_id: int) -> str:
    """Собирает callback_data вида "op:XXX|123""" 
    return f"{action}|{order_id}"


def parse_cb(data: str):
    """Парсит callback_data формата "op:XXX|123" и возвращает (action, order_id)"""
    try:
        action, id_str = (data or "").split("|", 1)
        return action, int(id_str)
    except Exception:
        return None, None

# Cancel confirm callbacks
CANCEL_YES = "cancel:YES"
CANCEL_NO = "cancel:NO"


