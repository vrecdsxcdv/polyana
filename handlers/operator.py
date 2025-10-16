"""
Обработчики для операторов (инлайн-кнопки).
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from database import get_db
from models import Order, OrderStatus
from services.callbacks import parse_cb, OP_TAKE, OP_READY, OP_NEEDS_FIX, OP_CONTACT
from texts import ORDER_TAKEN_BY_OPERATOR, ORDER_MARKED_READY, ORDER_NEEDS_FIX

logger = logging.getLogger(__name__)


async def operator_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, order_id = parse_cb(query.data or "")
    if not action or not order_id:
        return

    db = get_db()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            # Редактирование сообщений отключено для безопасности
            # await query.edit_message_text("Заказ не найден.")
            await context.bot.send_message(chat_id=query.message.chat_id, text="Заказ не найден.")
            return

        # клиент tg id
        user_tg_id = order.user.tg_user_id if hasattr(order, 'user') else None

        if action == OP_TAKE:
            order.status = OrderStatus.IN_PROGRESS
            order.needs_operator = False
            db.commit()
            # Редактирование сообщений отключено для безопасности
            # await query.edit_message_text(f"🛠 Заказ #{order.code} взят в работу.")
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"🛠 Заказ #{order.code} взят в работу.")
            if user_tg_id:
                try:
                    await context.bot.send_message(chat_id=user_tg_id, text=ORDER_TAKEN_BY_OPERATOR)
                except Exception:
                    logger.warning("Не удалось уведомить клиента о взятии в работу")

        elif action == OP_READY:
            order.status = OrderStatus.READY
            order.needs_operator = False
            db.commit()
            # Редактирование сообщений отключено для безопасности
            # await query.edit_message_text(f"✅ Заказ #{order.code} отмечен как готовый.")
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"✅ Заказ #{order.code} отмечен как готовый.")
            if user_tg_id:
                try:
                    await context.bot.send_message(chat_id=user_tg_id, text=ORDER_MARKED_READY)
                except Exception:
                    logger.warning("Не удалось уведомить клиента о готовности")

        elif action == OP_NEEDS_FIX:
            order.status = OrderStatus.WAITING_CLIENT
            order.needs_operator = True
            db.commit()
            # Редактирование сообщений отключено для безопасности
            # await query.edit_message_text(f"✏️ По заказу #{order.code} запрошены правки.")
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"✏️ По заказу #{order.code} запрошены правки.")
            if user_tg_id:
                try:
                    await context.bot.send_message(chat_id=user_tg_id, text=ORDER_NEEDS_FIX)
                except Exception:
                    logger.warning("Не удалось уведомить клиента о правках")

        elif action == OP_CONTACT:
            await query.answer("Откройте профиль клиента и напишите ему в личку", show_alert=True)

    except Exception as e:
        logger.exception("operator_callback fail: %s", e)
        try:
            await query.answer("Ошибка обработки", show_alert=True)
        except Exception:
            pass
    finally:
        db.close()


def get_operator_handlers():
    return [CallbackQueryHandler(operator_callback, pattern=r"^op:")]