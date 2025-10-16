from telegram import Update
from telegram.ext import ContextTypes
from db.session import SessionLocal
from db.models import Order

async def cb_view_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # чтобы Telegram не показывал "загрузка..."

    session = SessionLocal()
    try:
        # Parse order ID from callback data (format: "order:view:123")
        order_id = query.data.split(":")[-1]
        order = session.query(Order).filter(Order.id == order_id).first()

        if not order:
            await query.edit_message_text("❌ Заказ не найден или был удалён.")
            return

        text = (
            f"📦 *Ваш заказ №{order.id}*\n\n"
            f"Категория: {order.category}\n"
            f"Количество: {order.qty}\n"
            f"Статус: {order.status}\n"
            f"Комментарий: {order.comment or '—'}\n\n"
            f"🕒 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
        )

        await query.edit_message_text(
            text=text,
            parse_mode="Markdown"
        )

    except Exception as e:
        print("Ошибка при открытии заказа:", e)
        await query.edit_message_text("⚠️ Ошибка при открытии заказа. Попробуйте позже.")
    finally:
        session.close()




