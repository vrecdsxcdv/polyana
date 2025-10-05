"""
Уведомления для операторов.
"""

import os
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()
OPERATOR_CHAT_ID = os.getenv("OPERATOR_CHAT_ID")

async def notify_operator(bot: Bot, text: str):
    """Отправляет уведомление оператору в чат."""
    if OPERATOR_CHAT_ID:
        try:
            await bot.send_message(chat_id=int(OPERATOR_CHAT_ID), text=text)
        except Exception as e:
            # Логируем ошибку, но не падаем
            print(f"Ошибка отправки уведомления оператору: {e}")
