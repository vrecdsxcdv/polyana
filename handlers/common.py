import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import get_main_menu_keyboard, BTN_NEW_ORDER, BTN_MY_ORDERS, BTN_CALL_OPERATOR, BTN_HELP
from telegram import ReplyKeyboardMarkup

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["🧾 Новый заказ"],                          # весь ряд
            ["📦 Мои заказы", "🧑‍💼 Связаться с оператором"], # два по пол-ряда
            ["🆘 Помощь"],                               # весь ряд
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
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
    await (update.message or update.effective_message).reply_text(WELCOME, reply_markup=main_menu_keyboard())

help_command = start_command

async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = (update.message.text or "").strip()
    if t == BTN_NEW_ORDER:
        from handlers.order_flow import start_order
        return await start_order(update, context)
    if t == BTN_MY_ORDERS:
        return await my_orders_command(update, context)
    if t == BTN_CALL_OPERATOR:
        return await call_operator_command(update, context)
    if t == BTN_HELP:
        return await help_command(update, context)

async def my_orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает заказы текущего пользователя"""
    try:
        from services.orders import get_user_orders, STATUS_MAP
        from keyboards import get_main_menu_keyboard, make_orders_inline_kb
        
        user_id = update.effective_user.id
        orders = get_user_orders(user_id, limit=10)
        
        if not orders:
            await update.message.reply_text(
                "📦 У вас пока нет заказов.\n\nНажмите «🧾 Новый заказ» для оформления первого заказа!",
                reply_markup=main_menu_keyboard()
            )
            return
        
        message = "📦 Ваши заказы:\n\n"
        for order in orders:
            status_emoji = {
                "NEW": "🆕",
                "TAKEN": "📦", 
                "IN_PROGRESS": "⚙️",
                "COMPLETED": "✅",
                "DONE": "✅",
                "READY": "✅",
            }.get(order.status, "❓")
            status_text = STATUS_MAP.get(order.status or "NEW", order.status or "NEW")
            
            message += f"{status_emoji} <b>{order.code}</b> • {order.what_to_print} • {status_text}\n"
        kb = make_orders_inline_kb(orders)
        await update.message.reply_text(message, reply_markup=kb, parse_mode='HTML')
        
    except Exception as e:
        logger.exception("Error in my_orders_command: %s", e)
        await update.message.reply_text("⚠️ Техническая ошибка. Попробуйте ещё раз.", reply_markup=main_menu_keyboard())

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - показывает статус заказов пользователя"""
    await my_orders_command(update, context)

async def call_operator_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """NEW: Команда /call_operator - позвать оператора с обновленным текстом"""
    try:
        from handlers.common_contacts import CONTACT_TEXT, operator_keyboard
        
        # NEW: Обновленный текст для связи с оператором
        contact_text = (
            "💬 Связаться с оператором\n\n"
            "По любым вопросам вы можете написать напрямую оператору:\n"
            "👩‍💻 @polyanaprint\n"
            "📞 +7 963 163-92-62"
        )
        await update.message.reply_text(
            contact_text,
            reply_markup=operator_keyboard()
        )
    except Exception as e:
        logger.exception("Error in call_operator_command: %s", e)
        await update.message.reply_text("⚠️ Техническая ошибка. Попробуйте ещё раз.", reply_markup=main_menu_keyboard())

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /ping - диагностика доступности бота"""
    chat_id = update.effective_chat.id
    logger.info(f"Ping from chat_id: {chat_id}")
    await update.message.reply_text("pong")

async def whoami_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /whoami - показывает информацию о пользователе для отладки"""
    user = update.effective_user
    chat = update.effective_chat
    
    info = (
        f"👤 User ID: {user.id}\n"
        f"📝 Username: @{user.username or 'не указан'}\n"
        f"📛 First name: {user.first_name or 'не указан'}\n"
        f"📛 Last name: {user.last_name or 'не указан'}\n"
        f"💬 Chat ID: {chat.id}\n"
        f"💬 Chat type: {chat.type}"
    )
    
    logger.info(f"Whoami: user_id={user.id}, username={user.username}, chat_id={chat.id}")
    await update.message.reply_text(info)

async def error_handler(update:Update, context:ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled: %s", context.error)
    try:
        if update and update.effective_chat:
            await context.bot.send_message(update.effective_chat.id, "⚠️ Техническая ошибка. Попробуйте ещё раз.")
    except: pass