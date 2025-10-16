from telegram import Update
from telegram.ext import ContextTypes
from services.orders import get_order_by_code, format_order_for_user
from loguru import logger

async def cb_view_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    NEW: Показывает карточку заказа и статус по callback "order_view:<CODE>".
    Безопасность: показываем ТОЛЬКО если order.user_id == current_user.id
    """
    q = update.callback_query
    await q.answer()
    try:
        data = (q.data or "").strip()
        if not data.startswith("order_view:"):
            return
        code = data.split(":", 1)[1].strip()
        if not code:
            return

        # NEW: Надёжно получаем заказ из БД
        session_factory = context.bot_data.get("db_session_factory")
        session = session_factory() if session_factory else None
        try:
            if session is None:
                # Фоллбек: используем существующий хелпер, если фабрика не задана
                from services.orders import get_db
                session = get_db()
            order = get_order_by_code(session, code)
        finally:
            try:
                if session is not None:
                    session.close()
            except Exception:
                pass

        if not order:
            # NEW: Понятное сообщение об отсутствии заказа
            await q.message.reply_text("⚠️ Заказ не найден. Возможно, он был удалён или ещё не создан.")
            return

        if order.user_id != update.effective_user.id:
            await q.message.reply_text("⚠️ Недостаточно прав для просмотра этого заказа.")
            return

        # NEW: Отображаем карточку заказа
        text = format_order_for_user(order)
        await q.message.reply_text(text)
        
    except Exception as e:
        # NEW: Логируем ошибку и показываем дружелюбное сообщение
        logger.exception("Error in cb_view_order: %s", e)
        await q.message.reply_text("⚠️ Произошла ошибка при открытии заказа. Попробуйте позже.")




