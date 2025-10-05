"""
Общие обработчики команд бота.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from keyboards import get_home_keyboard, orders_list_inline, BTN_MY_ORDERS
from texts import WELCOME, HELP_MESSAGE, ERROR_MESSAGES, CONTACTS_MESSAGE, YOUR_ORDERS_TITLE, NO_ORDERS, STATUS_TITLES
from services.notifier import notify_operator_called
from services.orders import get_user_orders, get_order_by_id
from database import get_db
from models import Order, User
from services.notifier import NotifierService

logger = logging.getLogger(__name__)

# Дедупликация апдейтов
LAST_MSG_KEY = "__last_msg_id__"

def is_duplicate(update, context):
    msg = update.message or update.edited_message or update.callback_query
    if not msg:
        return False
    mid = getattr(msg, "message_id", None)
    if mid is None:
        return False
    key = f"{LAST_MSG_KEY}"
    if context.user_data.get(key) == mid:
        return True
    context.user_data[key] = mid
    return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    try:
        user = update.effective_user
        
        # Регистрируем пользователя в базе данных
        from database import get_db
        from models import User
        
        db = get_db()
        try:
            existing_user = db.query(User).filter(User.tg_user_id == user.id).first()
            
            if not existing_user:
                new_user = User(
                    tg_user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                db.add(new_user)
                db.commit()
                logger.info(f"Новый пользователь зарегистрирован: {user.id}")
            else:
                # Обновляем информацию о пользователе
                existing_user.username = user.username
                existing_user.first_name = user.first_name
                existing_user.last_name = user.last_name
                db.commit()
                
        except Exception as e:
            logger.error(f"Ошибка при регистрации пользователя {user.id}: {e}")
            db.rollback()
        finally:
            db.close()
        
        # Отправляем приветственное сообщение с безопасной клавиатурой
        try:
            await update.message.reply_text(
                WELCOME,
                reply_markup=get_home_keyboard(),
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке приветствия: {e}")
            # Fallback без клавиатуры
            await update.message.reply_text(WELCOME)
            
    except Exception as e:
        logger.error(f"Критическая ошибка в start_command: {e}")
        try:
            await update.message.reply_text("Привет! Я бот типографии 👋")
        except:
            pass


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    try:
        await update.message.reply_text(
            WELCOME,
            reply_markup=get_home_keyboard(),
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке помощи: {e}")
        try:
            await update.message.reply_text(WELCOME)
        except:
            pass


async def call_operator_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /call_operator."""
    user = update.effective_user
    
    try:
        # Попробуем отметить последний заказ пользователя как требующий оператора
        db = get_db()
        try:
            db_user = db.query(User).filter(User.tg_user_id == user.id).first()
            if db_user:
                order = db.query(Order).filter(Order.user_id == db_user.id).order_by(Order.created_at.desc()).first()
            else:
                order = None
            if order:
                order.needs_operator = True
                db.commit()
                await notify_operator_called(context.bot, order, order.user)
        finally:
            db.close()

        await update.message.reply_text(CONTACTS_MESSAGE, reply_markup=get_home_keyboard())
        
    except Exception as e:
        logger.error(f"Ошибка при вызове оператора: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при вызове оператора. Попробуйте позже.",
            reply_markup=get_home_keyboard()
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок."""
    import traceback
    
    # Логируем полный стектрейс
    err = "".join(traceback.format_exception(None, context.error, context.error.__traceback__))
    logger.error("Unhandled error: %s", err)
    
    # Безопасно отправляем сообщение пользователю только если это критическая ошибка
    try:
        if update and update.effective_chat:
            # Проверяем, не является ли это ошибкой в контексте диалога
            # В PTB v21 нет get_state, поэтому просто показываем мягкое сообщение
            
            # Только для критических ошибок показываем мягкое сообщение
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Произошла техническая ошибка. Попробуйте ещё раз."
            )
    except Exception as e:
        logger.error("Failed to send error to user: %s", e)


# Обработчики для заказов
async def my_orders_open(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Открывает список заказов пользователя."""
    user = update.effective_user
    
    try:
        items, has_more = get_user_orders(user.id, limit=10, offset=0)
        if not items:
            await (update.message or update.effective_message).reply_text(
                NO_ORDERS, reply_markup=get_home_keyboard()
            )
            return
        
        await (update.message or update.effective_message).reply_text(
            YOUR_ORDERS_TITLE, reply_markup=get_home_keyboard()
        )
        await (update.message or update.effective_message).reply_text(
            "Выберите заказ:", reply_markup=orders_list_inline(items, has_more)
        )
        # запомним смещение для "Показать ещё…"
        context.user_data["orders_offset"] = 0
        
    except Exception as e:
        logger.error(f"Ошибка при получении заказов: {e}")
        await (update.message or update.effective_message).reply_text(
            "❌ Ошибка при получении списка заказов. Попробуйте позже.",
            reply_markup=get_home_keyboard()
        )


async def my_orders_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает callback для списка заказов."""
    q = update.callback_query
    await q.answer()
    data = q.data
    
    try:
        if data == "ord:more":
            offset = context.user_data.get("orders_offset", 0) + 10
            context.user_data["orders_offset"] = offset
            items, has_more = get_user_orders(update.effective_user.id, limit=10, offset=offset)
            if not items:
                await q.edit_message_reply_markup(reply_markup=None)
                return
            await q.edit_message_reply_markup(reply_markup=orders_list_inline(items, has_more))
            return

        if data.startswith("ord:"):
            oid = int(data.split(":")[1])
            o = get_order_by_id(oid)
            if not o or o.user_id != update.effective_user.id:
                await q.edit_message_text("Заказ не найден.")
                return
            
            # покажем карточку этого заказа
            status = STATUS_TITLES.get(o.status.value, o.status.value)
            deadline_str = "Не указан"
            if o.deadline_at:
                deadline_str = o.deadline_at.strftime("%d.%m.%Y %H:%M")
            
            card = (
                f"📄 Заказ №{o.code}\n"
                f"Статус: {status}\n"
                f"Что печатать: {o.what_to_print}\n"
                f"Тираж: {o.quantity}\n"
                f"Формат: {o.format or 'Не указан'}\n"
                f"Стороны: {o.sides or 'Не указано'}\n"
                f"Дедлайн: {deadline_str}\n"
                f"Комментарий: {o.notes or '—'}\n"
            )
            await q.message.reply_text(card, reply_markup=get_home_keyboard())
            
    except Exception as e:
        logger.error(f"Ошибка при обработке callback заказов: {e}")
        await q.edit_message_text("❌ Ошибка при получении информации о заказе.")