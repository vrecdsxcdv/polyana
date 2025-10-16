import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.orders import update_order_status, get_order_by_code
from config import config

logger = logging.getLogger(__name__)

async def handle_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия кнопок статусов заказов"""
    query = update.callback_query
    await query.answer()
    
    if not query.data:
        return
    
    try:
        # Парсим callback_data
        parts = query.data.split('_')
        if len(parts) < 3:
            return
            
        action = parts[0]  # take, start_work, complete
        order_code = parts[-1]  # код заказа
        
        # Получаем информацию о пользователе
        user = query.from_user
        username = user.username or user.first_name or "Неизвестный"
        
        # Получаем заказ из базы
        order = get_order_by_code(order_code)
        if not order:
            # Редактирование сообщений отключено для безопасности
            # await query.edit_message_text("❌ Заказ не найден")
            await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Заказ не найден")
            return
        
        # Обновляем статус в зависимости от действия
        if action == "take":
            new_status = "TAKEN"
            status_text = f"📦 Заказ взят оператором @{username}"
        elif action == "start":
            new_status = "IN_PROGRESS" 
            status_text = f"⚙️ Оператор @{username} приступил к работе"
        elif action == "complete":
            new_status = "COMPLETED"
            status_text = f"✅ Заказ выполнен оператором @{username}"
        else:
            return
        
        # Обновляем статус в базе данных
        success = update_order_status(order.id, new_status, username)
        if not success:
            # Редактирование сообщений отключено для безопасности
            # await query.edit_message_text("❌ Ошибка обновления статуса")
            await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Ошибка обновления статуса")
            return
        
        # Обновляем сообщение с новым статусом
        original_text = query.message.text
        updated_text = original_text + f"\n\n{status_text}"
        
        # Убираем кнопки после завершения заказа
        if new_status == "COMPLETED":
            # Редактирование сообщений отключено для безопасности
            # await query.edit_message_text(updated_text)
            await context.bot.send_message(chat_id=query.message.chat_id, text=updated_text)
        else:
            # Обновляем кнопки для нового статуса
            keyboard = []
            if new_status == "TAKEN":
                keyboard = [
                    [
                        InlineKeyboardButton("⚙️ В работе", callback_data=f"start_work_{order_code}"),
                        InlineKeyboardButton("✅ Готово", callback_data=f"complete_order_{order_code}")
                    ]
                ]
            elif new_status == "IN_PROGRESS":
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Готово", callback_data=f"complete_order_{order_code}")
                    ]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            # Редактирование сообщений отключено для безопасности
            # await query.edit_message_text(updated_text, reply_markup=reply_markup)
            await context.bot.send_message(chat_id=query.message.chat_id, text=updated_text, reply_markup=reply_markup)
        
        # Уведомляем пользователя об изменении статуса
        try:
            user_message = f"📢 Статус вашего заказа {order_code} изменен: {status_text}"
            await context.bot.send_message(chat_id=order.user_id, text=user_message)
        except Exception as e:
            logger.warning(f"Failed to notify user {order.user_id}: {e}")
            
    except Exception as e:
        logger.exception(f"Error handling status callback: {e}")
        # Редактирование сообщений отключено для безопасности
        # await query.edit_message_text("❌ Произошла ошибка при обновлении статуса")
        await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Произошла ошибка при обновлении статуса")