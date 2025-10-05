"""
Сервис уведомлений операторов.
"""

import logging
from typing import Optional, List

from telegram import Bot
from telegram.error import TelegramError

from config import config
from services.formatting import FormattingService
from keyboards import get_operator_keyboard
from models import Attachment

logger = logging.getLogger(__name__)


class NotifierService:
    """Сервис уведомлений операторов."""
    
    def __init__(self):
        """Инициализация сервиса."""
        self.operator_chat_id = config.OPERATOR_CHAT_ID
    
    async def notify_new_order(self, bot: Bot, order, user) -> bool:
        """Уведомляет операторов о новом заказе."""
        if not self.operator_chat_id:
            return False
        
        try:
            message = FormattingService.format_order_card(order, user, for_operator=True)
            
            from keyboards import get_operator_keyboard
            keyboard = get_operator_keyboard(order.id)
            
            await bot.send_message(
                chat_id=self.operator_chat_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            logger.info(f"Уведомление о новом заказе {order.code} отправлено операторам")
            return True
            
        except TelegramError as e:
            logger.error(f"Ошибка при отправке уведомления о заказе: {e}")
            return False
    
    async def notify_operator_call(self, bot: Bot, user_id: int, username: Optional[str], 
                                 first_name: Optional[str], last_name: Optional[str], 
                                 message: str = "") -> bool:
        """Уведомляет операторов о вызове."""
        if not self.operator_chat_id:
            return False
        
        try:
            user_display = f"@{username}" if username else f"ID: {user_id}"
            if first_name or last_name:
                name = f"{first_name or ''} {last_name or ''}".strip()
                user_display += f" ({name})"
            
            notification_text = f"""
🚨 КЛИЕНТ ПРОСИТ ПОМОЩИ

👤 Пользователь: {user_display}
🆔 ID: {user_id}
"""
            
            if message:
                notification_text += f"\n💬 Сообщение: {message}"
            
            notification_text += "\n\n@all - новое обращение!"
            
            await bot.send_message(
                chat_id=self.operator_chat_id,
                text=notification_text,
                parse_mode='HTML'
            )
            
            logger.info(f"Уведомление о вызове оператора от пользователя {user_id} отправлено")
            return True
            
        except TelegramError as e:
            logger.error(f"Ошибка при отправке уведомления о вызове оператора: {e}")
            return False
    
    async def notify_client(self, bot: Bot, user_id: int, message: str) -> bool:
        """Отправляет уведомление клиенту."""
        try:
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Уведомление клиенту {user_id} отправлено")
            return True
            
        except TelegramError as e:
            logger.error(f"Ошибка при отправке уведомления клиенту: {e}")
            return False


# --- Дополнительные функции в стиле процедурного API ---

async def send_order_to_operators(bot: Bot, order, user):
    """Отправляет карточку и вложения (reply к карточке)."""
    import os
    OP = int(os.getenv("OPERATOR_CHAT_ID", "0") or "0")
    if not OP:
        return
    
    try:
        text = FormattingService.format_order_card(order, user, for_operator=True)
        card = await bot.send_message(OP, text=text, reply_markup=get_operator_keyboard(order.id))
        thread = card.message_id
        
        # Дублируем файлы, если есть
        for a in order.attachments or []:
            try:
                if a.tg_message_id and a.from_chat_id:
                    await bot.copy_message(
                        chat_id=OP, 
                        from_chat_id=a.from_chat_id, 
                        message_id=a.tg_message_id, 
                        reply_to_message_id=thread
                    )
                else:
                    await bot.send_document(
                        OP, 
                        document=a.file_id, 
                        filename=a.original_name or None, 
                        reply_to_message_id=thread
                    )
            except Exception:
                logger.exception("Forward attachment failed: order=%s attachment=%s", order.id, a.id)
    except Exception as e:
        logger.exception("send_order_to_operators fail: %s", e)


async def notify_operator_called(bot: Bot, order, user):
    operator_chat_id = config.OPERATOR_CHAT_ID
    if not operator_chat_id:
        return
    from texts import OPERATOR_NOTIF_PREFIX
    try:
        prefix = f"{OPERATOR_NOTIF_PREFIX}\n\n"
        text = prefix + FormattingService.format_order_card(order, user, for_operator=True)
        await bot.send_message(chat_id=int(operator_chat_id), text=text, reply_markup=get_operator_keyboard(order.id))
    except Exception as e:
        logger.exception("notify_operator_called fail: %s", e)