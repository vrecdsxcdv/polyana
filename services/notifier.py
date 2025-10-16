from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from services.formatting import format_order_summary

async def send_order_to_operators(bot, order, user, operator_chat_id, code):
    """Отправляет заказ в операторскую группу с кнопками статусов"""
    # Формируем карточку заказа
    order_summary = format_order_summary(order.__dict__ if hasattr(order, '__dict__') else order)
    
    # Добавляем информацию о пользователе
    user_info = f"👤 Клиент: {user.first_name or 'Пользователь'}"
    if user.username:
        user_info += f" (@{user.username})"
    user_info += f" (ID: {user.id})"
    
    text = f"📦 Новый заказ\n\n{order_summary}\n\n{user_info}\n\n🔢 Код заказа: <code>{code}</code>"
    
    # Создаем кнопки для управления статусом заказа
    keyboard = [
        [
            InlineKeyboardButton("📦 Взять", callback_data=f"take_order_{code}"),
            InlineKeyboardButton("⚙️ В работе", callback_data=f"start_work_{code}"),
            InlineKeyboardButton("✅ Готово", callback_data=f"complete_order_{code}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение
    message = await bot.send_message(
        chat_id=operator_chat_id, 
        text=text, 
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    # Отправляем PDF файлы, если есть
    if hasattr(order, 'attachments') and order.attachments:
        for attachment in order.attachments:
            try:
                await bot.send_document(
                    chat_id=operator_chat_id,
                    document=attachment.get('file_id'),
                    caption="📎 Макет PDF"
                )
            except Exception as e:
                print(f"Error sending attachment: {e}")
    
    return message