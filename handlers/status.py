"""
Обработчики для просмотра статуса заказов.
"""

from __future__ import annotations

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from database import get_db
from models import Order, User
from services.formatting import FormattingService
from keyboards import get_main_menu_keyboard
from texts import ERROR_MESSAGES, STATUS_EMPTY_LIST, STATUS_LIST_HEADER, STATUS_LIST_FOOTER, STATUS_ITEM_FMT, STATUS_LABELS

logger = logging.getLogger(__name__)


PAGE_SIZE = 5


def make_status_kb(page: int, pages: int):
    btns = []
    if page > 1:
        btns.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"status:{page-1}"))
    if page < pages:
        btns.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"status:{page+1}"))
    return InlineKeyboardMarkup([btns]) if btns else None


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_status_page(update, context, page=1)


async def handle_order_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает запрос на подробности заказа.
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    # Парсим номер заказа из сообщения
    text = update.message.text
    if not text or not text.startswith("📋 #"):
        return
    
    try:
        # Извлекаем номер заказа
        order_code = text.split(" - ")[0].replace("📋 #", "").strip()
        
        db = get_db()
        order = db.query(Order).filter(Order.code == order_code).first()
        
        if not order:
            await update.message.reply_text(
                "❌ Заказ не найден.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Проверяем, что заказ принадлежит пользователю
        user = update.effective_user
        if order.user.tg_user_id != user.id:
            await update.message.reply_text(
                "❌ У вас нет доступа к этому заказу.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Форматируем детальную карточку заказа
        card = FormattingService.format_order_card(order, order.user)
        
        await update.message.reply_text(card)
        
    except Exception as e:
        logger.error(f"Ошибка при получении деталей заказа: {e}")
        await update.message.reply_text(
            "❌ Ошибка при получении деталей заказа.",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        db.close()


async def status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    try:
        _, page_str = (q.data or "").split(":")
        page = int(page_str)
    except Exception:
        page = 1
    await show_status_page(update, context, page, edit=True)


async def show_status_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page=1, edit=False):
    user = update.effective_user
    db = get_db()
    try:
        db_user = db.query(User).filter(User.tg_user_id == user.id).first()
        if not db_user:
            text = STATUS_EMPTY_LIST
            if edit and update.callback_query:
                await update.callback_query.edit_message_text(text)
            else:
                await update.effective_message.reply_text(text)
            return

        total = db.query(Order).filter(Order.user_id == db_user.id).count()
        if total == 0:
            text = STATUS_EMPTY_LIST
            if edit and update.callback_query:
                await update.callback_query.edit_message_text(text)
            else:
                await update.effective_message.reply_text(text)
            return

        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page = max(1, min(page, pages))
        qs = (db.query(Order)
              .filter(Order.user_id == db_user.id)
              .order_by(Order.created_at.desc())
              .offset((page - 1) * PAGE_SIZE)
              .limit(PAGE_SIZE)
              .all())

        lines = [STATUS_LIST_HEADER, ""]
        for o in qs:
            lines.append(STATUS_ITEM_FMT.format(
                code=o.code, what=o.what_to_print, qty=o.quantity, status=STATUS_LABELS.get(o.status.value, o.status.value)
            ))
        lines.append("")
        lines.append(STATUS_LIST_FOOTER.format(page=page, pages=pages))
        text = "\n".join(lines)

        kb = make_status_kb(page, pages)
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=kb)
        else:
            await update.effective_message.reply_text(text, reply_markup=kb)

    finally:
        db.close()


async def handle_call_operator_for_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает вызов оператора для конкретного заказа.
    
    Args:
        update: Обновление от Telegram
        context: Контекст бота
    """
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("call_operator_"):
        return
    
    try:
        order_id = int(query.data.split("_")[-1])
        
        db = get_db()
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            await query.edit_message_text("❌ Заказ не найден.")
            return
        
        # Проверяем, что заказ принадлежит пользователю
        user = update.effective_user
        if order.user.tg_user_id != user.id:
            await query.edit_message_text("❌ У вас нет доступа к этому заказу.")
            return
        
        # Помечаем заказ как требующий внимания оператора
        order.needs_operator = True
        db.commit()
        
        # Уведомляем операторов
        from services.notifier import NotifierService
        notifier = NotifierService()
        await notifier.notify_operator_call(
            query.bot,
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            f"Пользователь просит помощи по заказу #{order.code}"
        )
        
        await query.edit_message_text(
            f"✅ Оператор уведомлен о вашем обращении по заказу #{order.code}."
        )
        
    except Exception as e:
        logger.error(f"Ошибка при вызове оператора для заказа: {e}")
        await query.edit_message_text("❌ Ошибка при вызове оператора.")
    finally:
        db.close()
