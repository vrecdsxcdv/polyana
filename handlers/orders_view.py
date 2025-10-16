from __future__ import annotations
import re
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from db.session import SessionLocal
from db.models import Order   # у нас именно db.models.Order

DETAILS_TMPL = (
    "📦 *Заказ №{id}*\n"
    "Категория: {category}\n"
    "Тираж: {qty}\n"
    "Формат: {format}\n"
    "Печать: {print_type}\n"
    "Ламинация: {lamination}\n"
    "Скругление углов: {corners}\n"
    "Цветность: {color}\n"
    "Телефон: {phone}\n"
    "Статус: *{status}*\n"
    "Комментарий: {comment}\n"
    "🕒 {created_at}\n"
)

def _extract_order_id(s: str) -> Optional[int]:
    """Достаём первое число из callback_data (поддержка разных форматов)."""
    if not s:
        return None
    m = re.search(r'(\d+)', s)
    return int(m.group(1)) if m else None

def _order_text(o: Order) -> str:
    def fmt(v, dash='—'):
        return v if (v is not None and f"{v}".strip() != "") else dash
    return DETAILS_TMPL.format(
        id=o.id,
        category=fmt(getattr(o, "category", None)),
        qty=fmt(getattr(o, "qty", None)),
        format=fmt(getattr(o, "paper_format", None)),
        print_type=fmt(getattr(o, "print_type", None)),
        lamination=fmt(getattr(o, "lamination", None)),
        corners=fmt(getattr(o, "corner_rounding", None)),
        color=fmt(getattr(o, "color", None)),
        phone=fmt(getattr(o, "phone", None)),
        status=fmt(getattr(o, "status", "Новый")),
        comment=fmt(getattr(o, "comment", None)),
        created_at=getattr(o, "created_at", None).strftime("%d.%m.%Y %H:%M") if getattr(o, "created_at", None) else "—",
    )

async def cb_view_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открыть заказ из списка. Без вечной загрузки, с защитой от ошибок."""
    query = update.callback_query
    # 1) мгновенно отвечаем, чтобы убрать «Загрузка…»
    try:
        await query.answer()
    except Exception:
        # даже если TG ругнётся, продолжаем — главное не падать
        pass

    data = query.data or ""
    order_id = _extract_order_id(data)

    if not order_id:
        try:
            await query.edit_message_text("❌ Не удалось определить номер заказа.")
        except Exception:
            await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Не удалось определить номер заказа.")
        return

    session = SessionLocal()
    try:
        order = session.query(Order).filter(Order.id == order_id).first()
        if not order:
            try:
                await query.edit_message_text("❌ Заказ не найден или был удалён.")
            except Exception:
                await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Заказ не найден или был удалён.")
            return

        text = _order_text(order)

        # стараемся редактировать исходное сообщение; если нельзя — шлём новое
        try:
            await query.edit_message_text(text=text, parse_mode="Markdown")
        except Exception:
            await context.bot.send_message(chat_id=query.message.chat_id, text=text, parse_mode="Markdown")

    except Exception as e:
        # аккуратный лог и дружелюбный текст пользователю
        print(f"[orders_view] error for order_id={order_id}: {e}")
        try:
            await query.edit_message_text("⚠️ Ошибка при открытии заказа. Попробуйте позже.")
        except Exception:
            await context.bot.send_message(chat_id=query.message.chat_id, text="⚠️ Ошибка при открытии заказа. Попробуйте позже.")
    finally:
        session.close()




