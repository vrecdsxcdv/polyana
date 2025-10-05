from telegram import Update
from telegram.ext import ContextTypes, CommandHandler


async def chatid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /chatid — всегда возвращает chat_id текущего чата"""
    chat = update.effective_chat
    await update.effective_message.reply_text(
        f"📎 chat_id этого чата: {chat.id}"
    )


def get_admin_handlers():
    return [
        CommandHandler("chatid", chatid_command),
    ]
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

load_dotenv()

# Загружаем ADMIN_IDS из .env и приводим к int
_ADMIN_IDS = {
    int(x) for x in (os.getenv("ADMIN_IDS") or "").split(",") if x.strip().isdigit()
}

def is_admin(user_id: int) -> bool:
    """Проверяем, является ли пользователь админом"""
    return user_id in _ADMIN_IDS

async def chatid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /chatid — показывает chat_id группы (только для админов)"""
    user_id = update.effective_user.id if update.effective_user else 0
    if not is_admin(user_id):
        await update.effective_message.reply_text("Команда доступна только администраторам.")
        return

    try:
        chat = update.effective_chat
        await update.effective_message.reply_text(
            f"📎 chat_id этого чата: `{chat.id}`",
            parse_mode="MarkdownV2"  # безопасный Markdown
        )
    except Exception as e:
        # Сообщаем пользователю мягко, а в логах будет реальная ошибка
        await update.effective_message.reply_text(
            "⚠️ Произошла техническая ошибка. Попробуйте ещё раз."
        )
        raise e

def get_admin_handlers():
    """Регистрируем все админские команды"""
    return [
        CommandHandler("chatid", chatid_command),
    ]