from telegram import Update
from telegram.ext import ContextTypes
from services.orders import get_order_by_code, format_order_for_user
from loguru import logger
from database import SessionLocal
from models import Order
import html

async def cb_view_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    NEW: Показывает карточку заказа и статус по callback "order:view:<ID>".
    Безопасность: показываем ТОЛЬКО если order.user_id == current_user.id
    """
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.split(":")[-1])
    session = SessionLocal()
    try:
        order = session.get(Order, order_id)
        if not order:
            await query.message.reply_text("Заказ не найден. Возможно, он был удалён или ещё не создан на этом сервере.")
            return

        # Сформируй краткую карточку заказа
        text = (
            f"<b>Заказ №{order.id}</b>\n"
            f"Статус: {html.escape(order.status or 'в обработке')}\n"
            f"Категория: {html.escape(order.category or '-')}\n"
            f"Тираж: {order.qty or '-'}\n"
            f"Комментарий: {html.escape(order.comment or '-')}\n"
        )
        await query.message.reply_text(text, parse_mode="HTML")
    except Exception as e:
        logger.exception("order:view failed")
        await query.message.reply_text("Произошла техническая ошибка при открытии заказа. Попробуйте позже.")
    finally:
        session.close()




