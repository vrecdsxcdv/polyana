"""
Обработчики диалога заказа (FSM).
"""

import logging
import re
import asyncio
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from states import OrderStates
from keyboards import (
    get_home_keyboard, get_product_keyboard, get_bc_qty_keyboard, get_bc_size_keyboard,
    get_sides_keyboard, get_fly_format_keyboard, get_upload_keyboard,
    get_notes_keyboard, get_confirm_keyboard, get_keyboard_remove, BTN_BC, BTN_FLY, BTN_BNR, BTN_PLK,
    BTN_STK, BTN_OTHER, BTN_1, BTN_2, BTN_BC_SIZE, BTN_BACK, BTN_CANCEL,
    BTN_NEXT, BTN_SKIP, BTN_SUBMIT, get_sheet_format_keyboard, get_postpress_keyboard,
    get_cancel_choice_keyboard, get_format_selection_keyboard, get_material_keyboard,
    get_print_color_keyboard, get_banner_size_keyboard, get_print_format_keyboard,
    get_print_type_keyboard, get_postpress_options_keyboard, get_smart_cancel_keyboard
)
from texts import (
    ASK_PRODUCT, ASK_BC_QTY, ASK_BC_SIZE, ASK_BC_SIDES, INFO_BC_PAPER,
    ASK_FLY_FORMAT, ASK_FLY_SIDES, UPLOAD_PROMPT, UPLOAD_OK,
    ASK_DUE, ASK_PHONE, ASK_NOTES, ERR_INT, ERR_BC_MIN, ERR_BC_STEP,
    ERR_ONLY_PDF, ERR_DATE, ERR_PHONE, REMIND_USE_BTNS,
    ASK_SHEET_FORMAT, ASK_CUSTOM_SIZE, ASK_POSTPRESS, ASK_BIGOVKA_COUNT, ASK_CANCEL_CHOICE,
    ERR_SIZE_FORMAT, ERR_SIZE_RANGE, ERR_BIGOVKA_INT, LAYOUT_HINT,
    ASK_BANNER_SIZE, ASK_MATERIAL, ASK_PRINT_COLOR
)
from services.validators import (
    to_int, is_multiple_of_50, parse_fly_choice, normalize_phone, parse_due,
    parse_custom_size, parse_bigovka_count, parse_banner_size, parse_custom_size_mm, parse_banner_size_m
)
from services.formatting import FormattingService
from services.notifier import send_order_to_operators
from services.normalize import is_btn, norm_btn, just_text
from database import get_db
from models import Order, User, Attachment, OrderStatus
from config import config
from handlers.common import is_duplicate

logger = logging.getLogger(__name__)

# Regex-паттерны для кнопок
BACK_RE = re.compile(r"^(?:⬅️?\s*Назад|Назад|/back|Back)$", re.IGNORECASE)
NEXT_RE = re.compile(r"^(?:➡️?\s*Далее|Далее)$", re.IGNORECASE)
SKIP_RE = re.compile(r"^(?:⏭️?\s*Пропустить|Пропустить)$", re.IGNORECASE)
SUBMIT_RE = re.compile(r"^(?:Готово)$", re.IGNORECASE)

# Ключи для стека состояний
HKEY = "__state_stack__"
CURKEY = "__current_state__"


def _stack(ctx):
    """Получает стек состояний из контекста."""
    return ctx.user_data.setdefault(HKEY, [])


def push_state(ctx, st):
    """Добавляет состояние в стек."""
    stck = _stack(ctx)
    if not stck or stck[-1] != st:
        stck.append(st)


def pop_state(ctx):
    """Извлекает предыдущее состояние из стека."""
    stck = _stack(ctx)
    if stck:
        stck.pop()
    return stck[-1] if stck else ConversationHandler.END


def set_cur(ctx, st):
    """Устанавливает текущее состояние."""
    ctx.user_data[CURKEY] = st


def get_cur(ctx):
    """Получает текущее состояние."""
    return ctx.user_data.get(CURKEY)


# Карта предыдущих состояний для безопасного fallback
PREV_OF = {
    OrderStates.BC_SIZE: OrderStates.BC_QTY,
    OrderStates.BC_SIDES: OrderStates.BC_SIZE,
    OrderStates.FLY_SIDES: OrderStates.FLY_FORMAT,
    OrderStates.ORDER_SHEET_FORMAT: OrderStates.PRODUCT,
    OrderStates.ORDER_CUSTOM_SIZE: OrderStates.ORDER_SHEET_FORMAT,
    OrderStates.ORDER_POSTPRESS: OrderStates.BC_SIDES,  # для визиток
    OrderStates.ORDER_POSTPRESS_BIGOVKA: OrderStates.ORDER_POSTPRESS,
    OrderStates.ORDER_UPLOAD: OrderStates.ORDER_POSTPRESS,
    OrderStates.ORDER_DUE: OrderStates.ORDER_UPLOAD,
    OrderStates.ORDER_PHONE: OrderStates.ORDER_DUE,
    OrderStates.ORDER_NOTES: OrderStates.ORDER_PHONE,
    OrderStates.ORDER_CONFIRM: OrderStates.ORDER_NOTES,
    OrderStates.PRINT_FORMAT: OrderStates.PRODUCT,
    OrderStates.PRINT_TYPE: OrderStates.PRINT_FORMAT,
}


async def handle_back(update, context):
    """Обработчик кнопки 'Назад'."""
    prev = pop_state(context)
    if prev == ConversationHandler.END:
        cur = get_cur(context)
        target = PREV_OF.get(cur)
        if not target:
            context.user_data.clear()
            return await render_state(update, context, OrderStates.PRODUCT)
        return await render_state(update, context, target)
    return await render_state(update, context, prev)


def wrong_button(update, kind: str):
    """Мягкое напоминание про кнопки."""
    asyncio.create_task((update.message or update.effective_message).reply_text(REMIND_USE_BTNS))
    return True


async def render_state(update, context, state):
    """Универсальная функция рендеринга состояния (без валидации)."""
    set_cur(context, state)
    reply = (update.message or update.effective_message).reply_text

    if state == OrderStates.PRODUCT:
        # Сначала удаляем старую клавиатуру, затем отправляем новую
        await reply("Обновляю меню…", reply_markup=get_keyboard_remove())
        await reply(ASK_PRODUCT, reply_markup=get_product_keyboard())
        return OrderStates.PRODUCT

    elif state == OrderStates.BC_QTY:
        await reply(ASK_BC_QTY, reply_markup=get_bc_qty_keyboard())
        return OrderStates.BC_QTY

    elif state == OrderStates.BC_SIZE:
        await reply(ASK_BC_SIZE, reply_markup=get_bc_size_keyboard())
        await reply(INFO_BC_PAPER)
        return OrderStates.BC_SIZE

    elif state == OrderStates.BC_SIDES:
        await reply(ASK_BC_SIDES, reply_markup=get_sides_keyboard())
        return OrderStates.BC_SIDES

    elif state == OrderStates.FLY_FORMAT:
        await reply(ASK_FLY_FORMAT, reply_markup=get_fly_format_keyboard())
        return OrderStates.FLY_FORMAT

    elif state == OrderStates.FLY_SIDES:
        await reply(ASK_FLY_SIDES, reply_markup=get_sides_keyboard())
        return OrderStates.FLY_SIDES

    elif state == OrderStates.ORDER_UPLOAD:
        await reply(UPLOAD_PROMPT.format(max_mb=25), reply_markup=get_upload_keyboard())
        return OrderStates.ORDER_UPLOAD

    elif state == OrderStates.ORDER_DUE:
        await reply(ASK_DUE, reply_markup=get_notes_keyboard())
        return OrderStates.ORDER_DUE

    elif state == OrderStates.ORDER_PHONE:
        await reply(ASK_PHONE, reply_markup=get_notes_keyboard())
        return OrderStates.ORDER_PHONE

    elif state == OrderStates.ORDER_NOTES:
        await reply(ASK_NOTES, reply_markup=get_notes_keyboard())
        return OrderStates.ORDER_NOTES

    elif state == OrderStates.ORDER_CONFIRM:
        order_summary = FormattingService.format_order_summary(context.user_data)
        await reply(
            f"✅ Подтверждение заказа\n\nПроверьте данные:\n\n{order_summary}",
            reply_markup=get_confirm_keyboard(),
        )
        return OrderStates.ORDER_CONFIRM

    # Новые состояния
    elif state == OrderStates.ORDER_SHEET_FORMAT:
        await reply(ASK_SHEET_FORMAT, reply_markup=get_format_selection_keyboard())
        return OrderStates.ORDER_SHEET_FORMAT

    elif state == OrderStates.ORDER_CUSTOM_SIZE:
        await reply(ASK_CUSTOM_SIZE, reply_markup=get_keyboard_remove())
        return OrderStates.ORDER_CUSTOM_SIZE

    elif state == OrderStates.ORDER_POSTPRESS:
        lamination = context.user_data.get("lamination", "none")
        bigovka_count = context.user_data.get("bigovka_count", 0)
        corner_rounding = context.user_data.get("corner_rounding", False)
        await reply(
            ASK_POSTPRESS,
            reply_markup=get_postpress_keyboard(lamination, bigovka_count, corner_rounding)
        )
        return OrderStates.ORDER_POSTPRESS

    elif state == OrderStates.ORDER_POSTPRESS_BIGOVKA:
        await reply(ASK_BIGOVKA_COUNT, reply_markup=get_keyboard_remove())
        return OrderStates.ORDER_POSTPRESS_BIGOVKA

    elif state == OrderStates.CANCEL_CHOICE:
        await reply(ASK_CANCEL_CHOICE, reply_markup=get_cancel_choice_keyboard())
        return OrderStates.CANCEL_CHOICE

    elif state == OrderStates.ORDER_BANNER_SIZE:
        await reply(ASK_BANNER_SIZE, reply_markup=get_banner_size_keyboard())
        return OrderStates.ORDER_BANNER_SIZE

    elif state == OrderStates.ORDER_MATERIAL:
        await reply(ASK_MATERIAL, reply_markup=get_material_keyboard())
        return OrderStates.ORDER_MATERIAL

    elif state == OrderStates.ORDER_PRINT_COLOR:
        await reply(ASK_PRINT_COLOR, reply_markup=get_print_color_keyboard())
        return OrderStates.ORDER_PRINT_COLOR

    elif state == OrderStates.PRINT_FORMAT:
        await reply("Выберите формат бумаги:", reply_markup=ReplyKeyboardMarkup(
            [["A4 (210×297 мм)", "A3 (297×420 мм)"],
             [BTN_BACK, BTN_CANCEL]],
            resize_keyboard=True
        ))
        return OrderStates.PRINT_FORMAT

    elif state == OrderStates.PRINT_TYPE:
        await reply("Выберите тип печати:", reply_markup=ReplyKeyboardMarkup(
            [["🖤 Чёрно-белая", "🎨 Цветная"],
             [BTN_BACK, BTN_CANCEL]],
            resize_keyboard=True
        ))
        return OrderStates.PRINT_TYPE

    # неизвестное состояние → главное меню
    context.user_data.clear()
    await reply("Чем ещё помочь?", reply_markup=get_home_keyboard())
    return ConversationHandler.END


async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог заказа."""
    context.user_data.clear()
    context.user_data["flow"] = "order"
    return await render_state(update, context, OrderStates.PRODUCT)


async def handle_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор продукта."""
    set_cur(context, OrderStates.PRODUCT)
    if is_duplicate(update, context):
        return get_cur(context) or ConversationHandler.END
    
    text = (update.message.text or "").strip()

    # Визитки → сначала тираж (минимум 50, кратно 50) → фикс. формат «90×50», бумага 300 г/м² → стороны → постобработка → загрузка PDF → срок → телефон → пожелания → подтверждение
    if is_btn(text, "визитки"):
        context.user_data["what_to_print"] = "Визитки"
        context.user_data["product_type"] = "bc"
        context.user_data["format"] = "90×50 мм"
        context.user_data["paper"] = "300 г/м²"
        set_cur(context, OrderStates.BC_QTY)
        push_state(context, OrderStates.BC_QTY)
        return await render_state(update, context, OrderStates.BC_QTY)

    # Флаеры → формат А7–А4 или Ваш размер (мм) → стороны → постобработка → загрузка PDF → … (далее как выше)
    if is_btn(text, "флаеры"):
        context.user_data["what_to_print"] = "Флаеры"
        context.user_data["product_type"] = "fly"
        set_cur(context, OrderStates.ORDER_SHEET_FORMAT)
        push_state(context, OrderStates.ORDER_SHEET_FORMAT)
        return await render_state(update, context, OrderStates.ORDER_SHEET_FORMAT)

    # Баннеры → ввод размера в метрах (0.1–20.0, без сторон) → постобработка → загрузка PDF → …
    if is_btn(text, "баннеры"):
        context.user_data["what_to_print"] = "Баннеры"
        context.user_data["product_type"] = "banner"
        set_cur(context, OrderStates.ORDER_BANNER_SIZE)
        push_state(context, OrderStates.ORDER_BANNER_SIZE)
        return await render_state(update, context, OrderStates.ORDER_BANNER_SIZE)

    # Плакаты → формат A3/A2/A1 или Ваш размер (мм) → стороны → постобработка → загрузка PDF → …
    if is_btn(text, "плакаты"):
        context.user_data["what_to_print"] = "Плакаты"
        context.user_data["product_type"] = "poster"
        set_cur(context, OrderStates.ORDER_SHEET_FORMAT)
        push_state(context, OrderStates.ORDER_SHEET_FORMAT)
        return await render_state(update, context, OrderStates.ORDER_SHEET_FORMAT)

    # Наклейки → формат A6–A3 или Ваш размер (мм) → материал: бумага/винил → цветность: Ч/Б или цвет → стороны (если уместно) → постобработка → загрузка PDF → …
    if is_btn(text, "наклейки"):
        context.user_data["what_to_print"] = "Наклейки"
        context.user_data["product_type"] = "sticker"
        set_cur(context, OrderStates.ORDER_SHEET_FORMAT)
        push_state(context, OrderStates.ORDER_SHEET_FORMAT)
        return await render_state(update, context, OrderStates.ORDER_SHEET_FORMAT)

    # Листы → формат A4/A3 → тип печати Ч/Б или цвет → стороны → загрузка PDF → …
    if is_btn(text, "листы"):
        context.user_data["what_to_print"] = "Листы"
        context.user_data["product_type"] = "sheets"
        set_cur(context, OrderStates.ORDER_SHEET_FORMAT)
        push_state(context, OrderStates.ORDER_SHEET_FORMAT)
        return await render_state(update, context, OrderStates.ORDER_SHEET_FORMAT)

    # Другое → свободный ввод описания → загрузка PDF (если есть) → …
    if is_btn(text, "другое"):
        context.user_data["what_to_print"] = "Другое"
        context.user_data["product_type"] = "other"
        set_cur(context, OrderStates.ORDER_SHEET_FORMAT)
        push_state(context, OrderStates.ORDER_SHEET_FORMAT)
        return await render_state(update, context, OrderStates.ORDER_SHEET_FORMAT)

    # Обработка кнопок навигации
    if is_btn(text, "назад"):
        return await handle_back(update, context)
    
    if is_btn(text, "отмена"):
        return await handle_cancel(update, context)

    # Если не распознали - мягкое напоминание
    await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_product_keyboard())
    return OrderStates.PRODUCT


async def handle_bc_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод тиража визиток."""
    set_cur(context, OrderStates.BC_QTY)
    if is_duplicate(update, context):
        return get_cur(context) or ConversationHandler.END
    text = (update.message.text or "").strip()

    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)

    n = to_int(text)
    if n is None:
        await update.message.reply_text(ERR_INT, reply_markup=get_bc_qty_keyboard())
        return OrderStates.BC_QTY

    if not is_multiple_of_50(n):
        # включает проверку минимум 50 и кратности 50
        await update.message.reply_text(ERR_BC_STEP, reply_markup=get_bc_qty_keyboard())
        return OrderStates.BC_QTY

    context.user_data["quantity"] = n
    set_cur(context, OrderStates.BC_SIZE)
    push_state(context, OrderStates.BC_SIZE)
    return await render_state(update, context, OrderStates.BC_SIZE)


async def handle_bc_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор размера визиток."""
    set_cur(context, OrderStates.BC_SIZE)
    if is_duplicate(update, context):
        return get_cur(context) or ConversationHandler.END
    text = (update.message.text or "").strip()

    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)

    if text == BTN_BC_SIZE:
        context.user_data["format"] = "90×50"
        context.user_data["paper"] = "300 г/м²"
        set_cur(context, OrderStates.BC_SIDES)
        push_state(context, OrderStates.BC_SIDES)
        return await render_state(update, context, OrderStates.BC_SIDES)

    await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_bc_size_keyboard())
    return OrderStates.BC_SIZE


async def handle_bc_sides(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор сторон печати визиток."""
    set_cur(context, OrderStates.BC_SIDES)
    if is_duplicate(update, context):
        return get_cur(context) or ConversationHandler.END
    text = (update.message.text or "").strip()

    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)

    if text == BTN_1:
        context.user_data["sides"] = "1"
    elif text == BTN_2:
        context.user_data["sides"] = "2"
    else:
        await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_sides_keyboard())
        return OrderStates.BC_SIDES

    # Переходим к постобработке
    set_cur(context, OrderStates.ORDER_POSTPRESS)
    push_state(context, OrderStates.ORDER_POSTPRESS)
    return await render_state(update, context, OrderStates.ORDER_POSTPRESS)


async def handle_fly_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор формата буклета."""
    set_cur(context, OrderStates.FLY_FORMAT)
    if is_duplicate(update, context):
        return get_cur(context) or ConversationHandler.END
    text = (update.message.text or "").strip()

    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)

    result = parse_fly_choice(text)
    if result:
        format_name, (w, h) = result
        context.user_data["format"] = f"{format_name} {w}×{h}"
        set_cur(context, OrderStates.FLY_SIDES)
        push_state(context, OrderStates.FLY_SIDES)
        return await render_state(update, context, OrderStates.FLY_SIDES)

    await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_fly_format_keyboard())
    return OrderStates.FLY_FORMAT


async def handle_fly_sides(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор сторон печати буклета."""
    set_cur(context, OrderStates.FLY_SIDES)
    if is_duplicate(update, context):
        return get_cur(context) or ConversationHandler.END
    text = (update.message.text or "").strip()

    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)

    if text == BTN_1:
        context.user_data["sides"] = "1"
    elif text == BTN_2:
        context.user_data["sides"] = "2"
    else:
        await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_sides_keyboard())
        return OrderStates.FLY_SIDES

    # Переходим к постобработке
    set_cur(context, OrderStates.ORDER_POSTPRESS)
    push_state(context, OrderStates.ORDER_POSTPRESS)
    return await render_state(update, context, OrderStates.ORDER_POSTPRESS)


async def handle_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает загрузку макета (только PDF)."""
    set_cur(context, OrderStates.ORDER_UPLOAD)
    if is_duplicate(update, context):
        return get_cur(context) or ConversationHandler.END

    # Документ
    if update.message.document:
        doc = update.message.document
        if not (doc.mime_type or "").startswith("application/pdf"):
            await update.message.reply_text(ERR_ONLY_PDF, reply_markup=get_upload_keyboard())
            return OrderStates.ORDER_UPLOAD

        context.user_data.setdefault("attachments", []).append({
            "file_id": doc.file_id,
            "file_unique_id": doc.file_unique_id,
            "original_name": doc.file_name or "document.pdf",
            "mime_type": doc.mime_type,
            "size": doc.file_size or 0,
            "tg_message_id": update.message.message_id,
            "from_chat_id": update.effective_chat.id,
            "kind": "document",
        })
        await update.message.reply_text(UPLOAD_OK, reply_markup=get_upload_keyboard())
        return OrderStates.ORDER_UPLOAD

    # Текстовые кнопки
    if update.message.text:
        text = update.message.text.strip()

        if text in (BTN_BACK, BTN_CANCEL):
            return await handle_back(update, context)

        if NEXT_RE.match(text):
            atts = context.user_data.get("attachments", [])
            has_pdf = any((a.get("mime_type") or "").startswith("application/pdf") for a in atts)
            if not has_pdf:
                await update.message.reply_text(ERR_ONLY_PDF, reply_markup=get_upload_keyboard())
                return OrderStates.ORDER_UPLOAD

            set_cur(context, OrderStates.ORDER_DUE)
            push_state(context, OrderStates.ORDER_DUE)
            return await render_state(update, context, OrderStates.ORDER_DUE)

        await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_upload_keyboard())
        return OrderStates.ORDER_UPLOAD

    await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_upload_keyboard())
    return OrderStates.ORDER_UPLOAD


async def handle_due(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод срока выполнения."""
    set_cur(context, OrderStates.ORDER_DUE)
    if is_duplicate(update, context):
        return get_cur(context) or ConversationHandler.END
    text = (update.message.text or "").strip()

    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)

    try:
        due_date = parse_due(text, config.TIMEZONE)
        if not due_date:
            await update.message.reply_text(ERR_DATE, reply_markup=get_notes_keyboard())
            return OrderStates.ORDER_DUE

        context.user_data["deadline_at"] = due_date
        set_cur(context, OrderStates.ORDER_PHONE)
        push_state(context, OrderStates.ORDER_PHONE)
        return await render_state(update, context, OrderStates.ORDER_PHONE)

    except Exception as e:
        logger.exception("Ошибка при парсинге даты: %s", e)
        await update.message.reply_text(ERR_DATE, reply_markup=get_notes_keyboard())
        return OrderStates.ORDER_DUE


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод телефона."""
    set_cur(context, OrderStates.ORDER_PHONE)
    if is_duplicate(update, context):
        return get_cur(context) or ConversationHandler.END
    text = (update.message.text or "").strip()

    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)

    phone = normalize_phone(text)
    if not phone:
        await update.message.reply_text(ERR_PHONE, reply_markup=get_notes_keyboard())
        return OrderStates.ORDER_PHONE

    context.user_data["contact"] = phone
    set_cur(context, OrderStates.ORDER_NOTES)
    push_state(context, OrderStates.ORDER_NOTES)
    return await render_state(update, context, OrderStates.ORDER_NOTES)


async def handle_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод пожеланий."""
    set_cur(context, OrderStates.ORDER_NOTES)
    if is_duplicate(update, context):
        return get_cur(context) or ConversationHandler.END
    text = (update.message.text or "").strip()

    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)

    if SKIP_RE.match(text) or not text:
        context.user_data["notes"] = ""
    else:
        context.user_data["notes"] = text[:1000]

    set_cur(context, OrderStates.ORDER_CONFIRM)
    push_state(context, OrderStates.ORDER_CONFIRM)
    return await render_state(update, context, OrderStates.ORDER_CONFIRM)


async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает подтверждение заказа."""
    set_cur(context, OrderStates.ORDER_CONFIRM)
    text = (update.message.text or "").strip()

    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)

    if SUBMIT_RE.match(text):
        success, order = await create_order(update, context)
        if success and order:
            # Успешное создание заказа
            success_message = (
                f"✅ <b>Заказ успешно создан!</b>\n\n"
                f"📋 <b>Номер заказа:</b> {order.code}\n"
                f"📝 <b>Что печатать:</b> {order.what_to_print}\n"
                f"🔢 <b>Тираж:</b> {order.quantity} шт.\n"
                f"📄 <b>Формат:</b> {order.format or 'Не указан'}\n\n"
                f"📞 <b>Наш оператор свяжется с вами в ближайшее время</b>\n"
                f"для уточнения деталей и расчета стоимости.\n\n"
                f"💬 Для связи с оператором используйте команду /call_operator"
            )
            await update.message.reply_text(
                success_message,
                reply_markup=get_home_keyboard(),
                parse_mode='HTML'
            )
            context.user_data.clear()
            return ConversationHandler.END
        else:
            # Ошибка создания заказа
            error_message = (
                "❌ <b>Ошибка при создании заказа</b>\n\n"
                "Произошла техническая ошибка. Пожалуйста:\n"
                "• Попробуйте создать заказ заново\n"
                "• Обратитесь к оператору: /call_operator\n"
                "• Или напишите нам в поддержку\n\n"
                "Приносим извинения за неудобства!"
            )
            await update.message.reply_text(
                error_message,
                reply_markup=get_home_keyboard(),
                parse_mode='HTML'
            )
            context.user_data.clear()
            return ConversationHandler.END

    await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_confirm_keyboard())
    return OrderStates.ORDER_CONFIRM


async def create_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Tuple[bool, Optional[Order]]:
    """Создает заказ в базе данных и шлёт уведомление операторам."""
    db = None
    try:
        db = get_db()
        user = update.effective_user

        # Проверяем существование таблиц
        try:
            # Проверяем, что таблицы существуют
            db.execute("SELECT 1 FROM users LIMIT 1")
            db.execute("SELECT 1 FROM orders LIMIT 1") 
            db.execute("SELECT 1 FROM attachments LIMIT 1")
        except Exception as table_error:
            logger.error(f"Ошибка доступа к таблицам: {table_error}")
            # Пытаемся создать таблицы
            from database import create_tables
            create_tables()

        # Пользователь
        db_user = db.query(User).filter(User.tg_user_id == user.id).first()
        if not db_user:
            db_user = User(
                tg_user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

        # Номер заказа
        order_code = generate_order_code()

        # Заказ
        order = Order(
            code=order_code,
            user_id=db_user.id,
            what_to_print=context.user_data.get("what_to_print", ""),
            quantity=context.user_data.get("quantity", 0),
            format=context.user_data.get("format", ""),
            sides=context.user_data.get("sides", ""),
            paper=context.user_data.get("paper", ""),
            deadline_at=context.user_data.get("deadline_at"),
            contact=context.user_data.get("contact", ""),
            notes=context.user_data.get("notes", ""),
            # Новые поля
            lamination=context.user_data.get("lamination", "none"),
            bigovka_count=context.user_data.get("bigovka_count", 0),
            corner_rounding=context.user_data.get("corner_rounding", False),
            sheet_format=context.user_data.get("sheet_format", ""),
            custom_size_mm=context.user_data.get("custom_size_mm", ""),
            material=context.user_data.get("material", ""),
            print_color=context.user_data.get("print_color", "color"),
            status=OrderStatus.NEW,
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # Вложения - сохраняем все, даже если их нет
        attachments_data = context.user_data.get("attachments", [])
        logger.info(f"Сохранение {len(attachments_data)} вложений для заказа {order.code}")
        
        for att in attachments_data:
            try:
                attachment = Attachment(
                    order_id=order.id,
                    file_id=att["file_id"],
                    file_unique_id=att.get("file_unique_id"),
                    original_name=att.get("original_name"),
                    mime_type=att.get("mime_type"),
                    size_bytes=att.get("size", 0),  # Используем size_bytes
                    size=att.get("size", 0),        # И size для совместимости
                    tg_message_id=att.get("tg_message_id"),
                    from_chat_id=att.get("from_chat_id"),
                    kind=att.get("kind", "document"),
                )
                db.add(attachment)
            except Exception as att_error:
                logger.error(f"Ошибка при сохранении вложения: {att_error}")
                # Продолжаем, даже если одно вложение не сохранилось

        db.commit()

        # Уведомление операторам
        try:
            await send_order_to_operators(context.bot, order, db_user)
            logger.info(f"Уведомление операторам отправлено для заказа {order.code}")
        except Exception as notify_error:
            logger.error(f"Ошибка при отправке уведомления операторам: {notify_error}")
            # Не прерываем создание заказа из-за ошибки уведомления

        logger.info(f"✅ Заказ {order.code} успешно создан")
        return True, order

    except Exception as e:
        logger.exception("Критическая ошибка при создании заказа: %s", e)
        if db:
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(f"Ошибка при откате транзакции: {rollback_error}")
        return False, None
    finally:
        if db:
            try:
                db.close()
            except Exception as close_error:
                logger.error(f"Ошибка при закрытии сессии БД: {close_error}")


def generate_order_code() -> str:
    """Генерирует номер заказа в формате YYMMDD-XXXX."""
    now = datetime.now()
    date_part = now.strftime("%y%m%d")
    db = get_db()
    try:
        today_orders = db.query(Order).filter(Order.code.like(f"{date_part}-%")).count()
        number_part = f"{today_orders + 1:04d}"
        return f"{date_part}-{number_part}"
    finally:
        db.close()


# Новые обработчики для форматов и постобработки

async def handle_sheet_format(update, context):
    """Обработчик выбора формата листа."""
    text = update.message.text.strip()
    product_type = context.user_data.get("product_type", "")
    
    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)
    
    # Обработка стандартных форматов
    if text == "A7 (105×74 мм)":
        context.user_data["sheet_format"] = "A7"
        context.user_data["format"] = "105×74"
    elif text == "A6 (148×105 мм)":
        context.user_data["sheet_format"] = "A6"
        context.user_data["format"] = "148×105"
    elif text == "A5 (210×148 мм)":
        context.user_data["sheet_format"] = "A5"
        context.user_data["format"] = "210×148"
    elif text == "A4 (297×210 мм)":
        context.user_data["sheet_format"] = "A4"
        context.user_data["format"] = "297×210"
    elif text == "A3 (420×297 мм)":
        context.user_data["sheet_format"] = "A3"
        context.user_data["format"] = "420×297"
    elif text == "A2 (594×420 мм)":
        context.user_data["sheet_format"] = "A2"
        context.user_data["format"] = "594×420"
    elif text == "A1 (841×594 мм)":
        context.user_data["sheet_format"] = "A1"
        context.user_data["format"] = "841×594"
    elif text == "Ваш размер":
        push_state(context, OrderStates.ORDER_SHEET_FORMAT)
        set_cur(context, OrderStates.ORDER_CUSTOM_SIZE)
        await update.message.reply_text(
            ASK_CUSTOM_SIZE,
            reply_markup=get_keyboard_remove()
        )
        return OrderStates.ORDER_CUSTOM_SIZE
    else:
        await update.message.reply_text(REMIND_USE_BTNS)
        return OrderStates.ORDER_SHEET_FORMAT
    
    # Определяем следующий шаг в зависимости от типа продукции
    push_state(context, OrderStates.ORDER_SHEET_FORMAT)
    
    if product_type == "sticker":
        # Для наклеек: формат → материал → цветность → стороны
        set_cur(context, OrderStates.ORDER_MATERIAL)
        await update.message.reply_text(
            ASK_MATERIAL,
            reply_markup=get_material_keyboard()
        )
        return OrderStates.ORDER_MATERIAL
    elif product_type == "sheets":
        # Для листов: формат → цветность → стороны
        set_cur(context, OrderStates.ORDER_PRINT_COLOR)
        await update.message.reply_text(
            ASK_PRINT_COLOR,
            reply_markup=get_print_color_keyboard()
        )
        return OrderStates.ORDER_PRINT_COLOR
    else:
        # Для остальных: формат → стороны
        set_cur(context, OrderStates.BC_SIDES)
        await update.message.reply_text(
            ASK_BC_SIDES,
            reply_markup=get_sides_keyboard()
        )
        return OrderStates.BC_SIDES


async def handle_custom_size(update, context):
    """Обработчик ввода пользовательского размера."""
    text = update.message.text.strip()
    product_type = context.user_data.get("product_type", "")
    
    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)
    
    size = parse_custom_size(text)
    if not size:
        await update.message.reply_text(ERR_SIZE_FORMAT)
        return OrderStates.ORDER_CUSTOM_SIZE
    
    width, height = size
    context.user_data["sheet_format"] = "custom"
    context.user_data["custom_size_mm"] = f"{width}×{height} мм"
    context.user_data["format"] = f"{width}×{height} мм"
    
    push_state(context, OrderStates.ORDER_CUSTOM_SIZE)
    
    # Определяем следующий шаг в зависимости от типа продукции
    if product_type == "sticker":
        # Для наклеек: размер → материал → цветность → стороны
        set_cur(context, OrderStates.ORDER_MATERIAL)
        await update.message.reply_text(
            ASK_MATERIAL,
            reply_markup=get_material_keyboard()
        )
        return OrderStates.ORDER_MATERIAL
    elif product_type == "sheets":
        # Для листов: размер → цветность → стороны
        set_cur(context, OrderStates.ORDER_PRINT_COLOR)
        await update.message.reply_text(
            ASK_PRINT_COLOR,
            reply_markup=get_print_color_keyboard()
        )
        return OrderStates.ORDER_PRINT_COLOR
    else:
        # Для остальных: размер → стороны
        set_cur(context, OrderStates.BC_SIDES)
        await update.message.reply_text(
            ASK_BC_SIDES,
            reply_markup=get_sides_keyboard()
        )
        return OrderStates.BC_SIDES


async def handle_postpress(update, context):
    """Обработчик выбора постпечатной обработки."""
    text = update.message.text.strip()

    lamination = context.user_data.get("lamination", "none")
    bigovka_count = context.user_data.get("bigovka_count", 0)
    corner_rounding = context.user_data.get("corner_rounding", False)

    if text.startswith("Ламинация"):
        if "(мат)" in text:
            context.user_data["lamination"] = "matte"
        elif "(глянец)" in text:
            context.user_data["lamination"] = "glossy"
        else:
            context.user_data["lamination"] = "none"
        return await render_state(update, context, OrderStates.ORDER_POSTPRESS)

    elif text == "Биговка" or text.startswith("Биговка ("):
        push_state(context, OrderStates.ORDER_POSTPRESS)
        set_cur(context, OrderStates.ORDER_POSTPRESS_BIGOVKA)
        await update.message.reply_text(ASK_BIGOVKA_COUNT, reply_markup=get_keyboard_remove())
        return OrderStates.ORDER_POSTPRESS_BIGOVKA

    elif text.startswith("Скругление углов"):
        context.user_data["corner_rounding"] = not corner_rounding
        return await render_state(update, context, OrderStates.ORDER_POSTPRESS)

    elif text == "Без обработки":
        context.user_data.update({
            "lamination": "none",
            "bigovka_count": 0,
            "corner_rounding": False
        })
        # остаёмся на шаге постобработки
        return await render_state(update, context, OrderStates.ORDER_POSTPRESS)

    elif text == "➡️ Далее":
        push_state(context, OrderStates.ORDER_POSTPRESS)
        set_cur(context, OrderStates.ORDER_UPLOAD)
        await update.message.reply_text(
            f"{UPLOAD_PROMPT.format(max_mb=config.MAX_UPLOAD_MB)}\n\n{LAYOUT_HINT}",
            reply_markup=get_upload_keyboard()
        )
        return OrderStates.ORDER_UPLOAD

    elif text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)

    else:
        await update.message.reply_text(
            REMIND_USE_BTNS,
            reply_markup=get_postpress_keyboard(
                context.user_data.get("lamination", "none"),
                context.user_data.get("bigovka_count", 0),
                context.user_data.get("corner_rounding", False),
            )
        )
        return OrderStates.ORDER_POSTPRESS


async def handle_postpress_bigovka(update, context):
    """Обработчик ввода количества линий биговки."""
    text = update.message.text.strip()

    count = parse_bigovka_count(text)
    if count is None:
        await update.message.reply_text(
            ERR_BIGOVKA_INT,
            reply_markup=get_postpress_keyboard(
                context.user_data.get("lamination", "none"),
                context.user_data.get("bigovka_count", 0),
                context.user_data.get("corner_rounding", False),
            )
        )
        return OrderStates.ORDER_POSTPRESS_BIGOVKA

    context.user_data["bigovka_count"] = count

    await update.message.reply_text(
        f"✅ Биговка ({count} линий) сохранена."
    )
    # Возвращаемся в меню постобработки, ничего не сбрасывая
    return await render_state(update, context, OrderStates.ORDER_POSTPRESS)


async def handle_cancel_choice(update, context):
    """Обработчик выбора типа отмены."""
    text = update.message.text.strip()
    
    if text == "↩️ Только этот шаг":
        # Возвращаемся на предыдущий шаг
        prev = pop_state(context)
        if prev == ConversationHandler.END:
            cur = get_cur(context)
            target = PREV_OF.get(cur)
            if not target:
                context.user_data.clear()
                await update.message.reply_text(
                    "❌ Не удалось вернуться к предыдущему шагу",
                    reply_markup=get_home_keyboard()
                )
                return ConversationHandler.END
            set_cur(context, target)
        else:
            set_cur(context, prev)
        
        # Рендерим состояние
        await render_state(update, context)
        return get_cur(context)
        
    elif text == "🗑 Полностью отменить заказ":
        # Полный сброс
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Заказ отменен",
            reply_markup=get_home_keyboard()
        )
        return ConversationHandler.END
    
    else:
        await update.message.reply_text(REMIND_USE_BTNS)
        return OrderStates.CANCEL_CHOICE


async def handle_cancel(update, context):
    """Обработчик кнопки 'Отмена' - показывает выбор типа отмены."""
    await update.message.reply_text(
        ASK_CANCEL_CHOICE,
        reply_markup=get_cancel_choice_keyboard()
    )
    return OrderStates.CANCEL_CHOICE


# Новые обработчики для расширенных типов продукции

async def handle_banner_size(update, context):
    """Обработчик ввода размера баннера."""
    text = update.message.text.strip()
    
    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)
    
    size = parse_banner_size(text)
    if not size:
        await update.message.reply_text("❌ Неверный формат размера. Введите размер в метрах, например: 2×1.5")
        return OrderStates.ORDER_BANNER_SIZE
    
    width, height = size
    context.user_data["sheet_format"] = "custom"
    context.user_data["custom_size_mm"] = f"{width}×{height} м"
    context.user_data["format"] = f"{width}×{height} м"
    
    # Для баннеров нет выбора сторон, сразу к постобработке
    push_state(context, OrderStates.ORDER_BANNER_SIZE)
    set_cur(context, OrderStates.ORDER_POSTPRESS)
    return await render_state(update, context, OrderStates.ORDER_POSTPRESS)


async def handle_material(update, context):
    """Обработчик выбора материала для наклеек."""
    text = update.message.text.strip()
    
    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)
    
    if text == "📄 Бумага":
        context.user_data["material"] = "paper"
    elif text == "🎯 Винил":
        context.user_data["material"] = "vinyl"
    else:
        await update.message.reply_text(REMIND_USE_BTNS)
        return OrderStates.ORDER_MATERIAL
    
    # Переходим к выбору цветности
    push_state(context, OrderStates.ORDER_MATERIAL)
    set_cur(context, OrderStates.ORDER_PRINT_COLOR)
    return await render_state(update, context, OrderStates.ORDER_PRINT_COLOR)


async def handle_print_color(update, context):
    """Обработчик выбора цветности печати."""
    text = update.message.text.strip()
    
    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)
    
    if text == "🎨 Цветная":
        context.user_data["print_color"] = "color"
    elif text == "⚫ Ч/Б":
        context.user_data["print_color"] = "bw"
    else:
        await update.message.reply_text(REMIND_USE_BTNS)
        return OrderStates.ORDER_PRINT_COLOR
    
    # Переходим к выбору сторон
    push_state(context, OrderStates.ORDER_PRINT_COLOR)
    set_cur(context, OrderStates.BC_SIDES)
    return await render_state(update, context, OrderStates.BC_SIDES)


# Обработчики для обычной печати

async def handle_print_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора формата для обычной печати."""
    text = update.message.text.strip()
    
    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)
    
    if text == "A4 (210×297 мм)":
        context.user_data["sheet_format"] = "A4"
        context.user_data["format"] = "210×297"
    elif text == "A3 (297×420 мм)":
        context.user_data["sheet_format"] = "A3"
        context.user_data["format"] = "297×420"
    else:
        await update.message.reply_text("Пожалуйста, выберите один из форматов.")
        return OrderStates.PRINT_FORMAT
    
    # Переходим к выбору типа печати
    push_state(context, OrderStates.PRINT_FORMAT)
    set_cur(context, OrderStates.PRINT_TYPE)
    await update.message.reply_text(
        "Выберите тип печати:",
        reply_markup=ReplyKeyboardMarkup(
            [["🖤 Чёрно-белая", "🎨 Цветная"],
             [BTN_BACK, BTN_CANCEL]],
            resize_keyboard=True
        )
    )
    return OrderStates.PRINT_TYPE


async def handle_print_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора типа печати."""
    text = update.message.text.strip().lower()
    
    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)
    
    if "чёр" in text or "черн" in text:
        context.user_data["print_color"] = "bw"
    elif "цвет" in text:
        context.user_data["print_color"] = "color"
    else:
        await update.message.reply_text("Выберите, пожалуйста, тип печати.")
        return OrderStates.PRINT_TYPE
    
    # Переходим к загрузке файла
    push_state(context, OrderStates.PRINT_TYPE)
    set_cur(context, OrderStates.ORDER_UPLOAD)
    await update.message.reply_text(
        f"Прикрепите ваш файл для печати (PDF до {config.MAX_UPLOAD_MB} МБ).",
        reply_markup=get_upload_keyboard()
    )
    return OrderStates.ORDER_UPLOAD


# Новые обработчики для обычной печати

async def handle_print_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обычная печать: выбор формата."""
    await update.message.reply_text(
        "Выберите формат бумаги:",
        reply_markup=get_print_format_keyboard()
    )
    return OrderStates.PRINT_FORMAT


async def handle_print_format_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора формата для обычной печати (новая версия)."""
    text = update.message.text.strip()
    
    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)
    
    if text == "A4 (210×297 мм)":
        context.user_data["format"] = "A4"
        context.user_data["sheet_format"] = "A4"
    elif text == "A3 (297×420 мм)":
        context.user_data["format"] = "A3"
        context.user_data["sheet_format"] = "A3"
    else:
        await update.message.reply_text("Выберите формат из списка.")
        return OrderStates.PRINT_FORMAT

    await update.message.reply_text(
        "Выберите тип печати:",
        reply_markup=get_print_type_keyboard()
    )
    return OrderStates.PRINT_TYPE


async def handle_print_type_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора типа печати (новая версия)."""
    text = update.message.text.strip().lower()
    
    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)
    
    if "чёр" in text or "черн" in text:
        context.user_data["print_color"] = "bw"
    elif "цвет" in text:
        context.user_data["print_color"] = "color"
    else:
        await update.message.reply_text("Выберите, пожалуйста, тип печати.")
        return OrderStates.PRINT_TYPE

    await update.message.reply_text(
        "Выберите дополнительные параметры:",
        reply_markup=get_postpress_options_keyboard()
    )
    return OrderStates.POSTPRESS


async def handle_postpress_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора дополнительных параметров постобработки."""
    text = update.message.text.strip()
    
    if text in (BTN_BACK, BTN_CANCEL):
        return await handle_back(update, context)
    
    if text == "✨ Ламинация (мат)":
        context.user_data["lamination"] = "matte"
    elif text == "✨ Ламинация (глянец)":
        context.user_data["lamination"] = "glossy"
    elif text == "➖ Биговка":
        context.user_data["bigovka_count"] = 1
    elif text == "🔘 Скругление углов":
        context.user_data["corner_rounding"] = True
    elif text == "Нет":
        # Сбрасываем все параметры
        context.user_data["lamination"] = "none"
        context.user_data["bigovka_count"] = 0
        context.user_data["corner_rounding"] = False
    
    # Переходим к загрузке файла
    push_state(context, OrderStates.POSTPRESS)
    set_cur(context, OrderStates.ORDER_UPLOAD)
    await update.message.reply_text(
        f"Прикрепите ваш файл для печати (PDF до {config.MAX_UPLOAD_MB} МБ).",
        reply_markup=get_upload_keyboard()
    )
    return OrderStates.ORDER_UPLOAD


# Умная отмена

async def handle_smart_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена шага или всего заказа."""
    await update.message.reply_text(
        "❓ Отменить текущий шаг или весь заказ?",
        reply_markup=get_smart_cancel_keyboard()
    )
    context.user_data["cancel_query"] = True
    return OrderStates.CANCEL_CHOICE


async def handle_cancel_choice_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик выбора типа отмены (новая версия)."""
    text = update.message.text.strip()
    
    if text == "↩️ Только шаг":
        # Возвращаемся на предыдущий шаг
        prev = pop_state(context)
        if prev == ConversationHandler.END:
            cur = get_cur(context)
            target = PREV_OF.get(cur)
            if not target:
                context.user_data.clear()
                await update.message.reply_text(
                    "❌ Не удалось вернуться к предыдущему шагу",
                    reply_markup=get_home_keyboard()
                )
                return ConversationHandler.END
            set_cur(context, target)
        else:
            set_cur(context, prev)
        
        # Рендерим состояние
        await render_state(update, context)
        return get_cur(context)
        
    elif text == "🗑 Весь заказ":
        # Полный сброс
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Заказ отменен",
            reply_markup=get_home_keyboard()
        )
        return ConversationHandler.END
    
    else:
        await update.message.reply_text(REMIND_USE_BTNS)
        return OrderStates.CANCEL_CHOICE