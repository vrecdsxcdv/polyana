import html
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes
from db.session import SessionLocal
from db.models import Order

async def cb_view_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, _, order_id_str = query.data.split(":")
        order_id = int(order_id_str)
    except Exception:
        await query.message.reply_text("Некорректный идентификатор заказа.")
        return

    session = SessionLocal()
    try:
        order = session.get(Order, order_id)
        if not order:
            await query.message.reply_text("Заказ не найден. Возможно, он удалён или ещё не создан.")
            return

        text = (
            f"<b>Заказ №{order.id}</b>\n"
            f"Статус: {html.escape(order.status or 'в обработке')}\n"
            f"Категория: {html.escape(order.what_to_print or '-')}\n"
            f"Тираж: {order.quantity or '-'}\n"
            f"Комментарий: {html.escape(order.notes or '-')}\n"
            f"Создан: {order.created_at:%Y-%m-%d %H:%M}"
        )
        await query.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception:
        logger.exception("order:view failed")
        await query.message.reply_text("Техническая ошибка при открытии заказа. Попробуйте позже.")
    finally:
        session.close()




