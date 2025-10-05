# handlers/menu_handlers.py
from telegram import Update
from telegram.ext import ContextTypes

# Переиспользуем уже существующие обработчики из проекта
from .common import my_orders_open as handle_my_orders
from .common import help_command as handle_help
from .common import call_operator_command as handle_contact_operator
from .order_flow import start_order as handle_new_order

__all__ = [
    "handle_my_orders",
    "handle_new_order",
    "handle_contact_operator",
    "handle_help",
]


