# new file
from telegram import Update
from telegram.ext import ContextTypes
from texts import CONTACTS_TEXT
from keyboards import contact_operator_kb

async def handle_contact_operator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q:
        await q.answer()
        await q.edit_message_reply_markup(reply_markup=None)
        await q.message.reply_text(CONTACTS_TEXT, reply_markup=contact_operator_kb())
    else:
        await update.effective_message.reply_text(CONTACTS_TEXT, reply_markup=contact_operator_kb())
