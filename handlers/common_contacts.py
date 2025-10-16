# new file
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# NEW: Фиксированные контакты оператора
OPERATOR_USERNAME = "polyanaprint"
OPERATOR_PHONE = "+7 963 163-92-62"

# NEW: Текст для связи с оператором
CONTACT_TEXT = (
    "💬 Связаться с оператором\n\n"
    "Для оформления индивидуального заказа напишите напрямую:\n"
    f"👩‍💻 @{OPERATOR_USERNAME}\n"
    f"📞 {OPERATOR_PHONE}\n\n"
    "🔹 Нажмите кнопку ниже, чтобы открыть чат с оператором:"
)

def operator_keyboard():
    """NEW: Клавиатура с кнопкой для открытия чата с оператором"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("💬 Открыть чат с оператором", url=f"https://t.me/{OPERATOR_USERNAME}")
    ]])

async def handle_contact_operator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """NEW: Обработчик кнопки 'Связаться с оператором' с завершением диалога"""
    q = update.callback_query
    if q:
        await q.answer()
        await q.edit_message_reply_markup(reply_markup=None)
        
        # NEW: Отправляем финальное сообщение с контактами
        await q.message.reply_text(CONTACT_TEXT, reply_markup=operator_keyboard())
        
        # NEW: Завершаем ConversationHandler
        return ConversationHandler.END
    else:
        # Fallback для обычных сообщений
        await update.effective_message.reply_text(CONTACT_TEXT, reply_markup=operator_keyboard())
