import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_home_keyboard
from texts import WELCOME

logger=logging.getLogger(__name__)
LAST_MSG_KEY="__last_msg_id__"

def is_duplicate(update, context):
    msg = update.message or update.edited_message or update.callback_query
    if not msg: return False
    mid = getattr(msg, "message_id", None)
    if mid is None: return False
    if context.user_data.get(LAST_MSG_KEY)==mid: return True
    context.user_data[LAST_MSG_KEY]=mid; return False

async def start_command(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await (update.message or update.effective_message).reply_text(WELCOME, reply_markup=get_home_keyboard())

help_command = start_command

async def error_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled: %s", context.error)
    try:
        if update and update.effective_chat:
            await context.bot.send_message(update.effective_chat.id, "⚠️ Техническая ошибка. Попробуйте ещё раз.")
    except: pass