# handlers/order_flow.py
import logging
import re
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes, ConversationHandler
from states import OrderStates

# --- safe reply + anti-duplicate ---------------------------------
from telegram import Message

def eff_msg(update) -> Message:
    return update.effective_message

def _screen_fingerprint(state, text):
    return f"{state}|{(text or '').strip()}"

async def say(update, text, *, reply_markup=None, parse_mode=None, state_for_dedupe=None, context=None):
    """
    Единая отправка сообщений:
    - не редактирует и не удаляет;
    - гасит точные дубли одного и того же экрана (state+text).
    """
    try:
        if context is not None and state_for_dedupe is not None:
            fp = _screen_fingerprint(state_for_dedupe, text)
            last = context.user_data.get("last_screen_fp")
            if last == fp:
                # тот же экран уже показан — не дублируем
                return None
            context.user_data["last_screen_fp"] = fp

        return await eff_msg(update).reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        return await eff_msg(update).reply_text("⚠️ Техническая ошибка. Попробуйте ещё раз.")

# ✅ Безопасный вывод шага без дублей сообщений
async def render(update, context, text, reply_markup=None, parse_mode=None):
    """
    Отправляет сообщение шага, удаляя предыдущее системное сообщение,
    чтобы избежать дублирования (например: дважды 'Формат визиток').
    """
    # Удаление сообщений отключено для безопасности
    # last_id = context.user_data.pop("last_step_msg_id", None)
    # if last_id:
    #     try:
    #         await context.bot.delete_message(
    #             chat_id=update.effective_chat.id,
    #             message_id=last_id
    #         )
    #     except Exception:
    #         pass

    msg = await say(update, text, reply_markup=reply_markup, parse_mode=parse_mode)
    context.user_data["last_step_msg_id"] = msg.message_id
    return msg

# --- stack helpers если они уже есть, оставляем как есть ---
def _stack(ctx): return ctx.user_data.setdefault("state_stack", [])
def push_state(ctx, st):
    s = _stack(ctx)
    if not s or s[-1] != st:
        s.append(st)
def pop_state(ctx):
    s = _stack(ctx)
    return s.pop() if s else None
def top_state(ctx):
    s = _stack(ctx)
    return s[-1] if s else None

async def goto(update, context, state, renderer):
    # перед каждым новым экраном сбрасываем анти-дедуп,
    # чтобы новый шаг гарантированно отрисовался
    context.user_data.pop("last_screen_fp", None)
    push_state(context, state)
    await renderer(update, context)  # renderer внутри вызовет say(..., state_for_dedupe=state, context=context)
    return state

# ✅ Вспомогательные функции для проверки файлов
def _get_ext(filename: str) -> str:
    return (filename or "").rsplit(".", 1)[-1].lower() if "." in (filename or "") else ""

ALLOWED_COMMON_EXTS = {"pdf", "jpg", "jpeg", "png"}

# --- РЕНДЕРЕР ШАГОВ ---

# Каждая функция ниже должна отправлять сообщение и нужную reply-клавиатуру,
# и НИЧЕГО не менять в данных заказа.
# Если у тебя такие функции уже есть — просто укажи их в словаре.

async def render_choose_category(update, context):
    from keyboards import get_categories_keyboard
    await say(
        update,
        "Что будем печатать?",
        reply_markup=get_categories_keyboard(),
        state_for_dedupe=OrderStates.CHOOSE_CATEGORY,
        context=context,
    )

# -------- ВИЗИТКИ --------
async def render_bc_qty(update, context):
    from keyboards import nav_keyboard
    await say(
        update,
        "📊 Укажите тираж визиток (кратно 50, минимум 50). Подсказки: 50, 100, 150, 200, 500, 1000.",
        reply_markup=nav_keyboard(),
        state_for_dedupe=OrderStates.BC_QTY,
        context=context,
    )

async def render_bc_format(update, context):
    from keyboards import get_bc_format_keyboard
    await say(
        update,
        "📐 Формат визиток:",
        reply_markup=get_bc_format_keyboard(),
        state_for_dedupe=OrderStates.BC_FORMAT,
        context=context,
    )

async def render_bc_sides(update, context):
    from keyboards import get_bc_sides_keyboard
    await say(
        update,
        "🖨️ Стороны печати визиток:",
        reply_markup=get_bc_sides_keyboard(),
        state_for_dedupe=OrderStates.BC_SIDES,
        context=context,
    )

async def render_bc_lamination(update, context):
    from keyboards import get_bc_lamination_keyboard
    await say(
        update,
        "✨ Ламинация визиток:",
        reply_markup=get_bc_lamination_keyboard(),
        state_for_dedupe=OrderStates.BC_LAMINATION,
        context=context,
    )

async def ask_bc_files(update, context):
    from keyboards import get_files_keyboard
    return await render(update, context, "📎 Загрузите макет (только PDF). Затем нажмите «➡️ Далее».", reply_markup=get_files_keyboard())

async def render_common_files(update, context):
    from keyboards import get_files_keyboard
    category = context.user_data.get("category", "")
    if category == "business_card":
        text = "📎 Загрузите макет (только PDF). Затем нажмите «➡️ Далее»."
    else:
        text = "📎 Загрузите макет (PDF/JPG/PNG). Затем нажмите «➡️ Далее»."
    
    await say(
        update,
        text,
        reply_markup=get_files_keyboard(),
        state_for_dedupe=OrderStates.ORDER_FILES,
        context=context,
    )

# -------- ОФИСНАЯ ПЕЧАТЬ --------
async def render_office_copies(update, context):
    from keyboards import nav_keyboard
    await say(
        update,
        "🧾 Укажите количество экземпляров (можно цифрами или словами: \"3\", \"три\", \"пять\").",
        reply_markup=nav_keyboard(),
        state_for_dedupe=OrderStates.QUANTITY,
        context=context,
    )

async def render_office_format(update, context):
    from keyboards import get_office_format_keyboard
    await say(
        update,
        "📄 Выберите формат: A4 или A3",
        reply_markup=get_office_format_keyboard(),
        state_for_dedupe=OrderStates.OFFICE_FORMAT,
        context=context,
    )

async def render_office_color(update, context):
    from keyboards import get_office_color_keyboard
    await say(
        update,
        "🎨 Выберите цветность печати:",
        reply_markup=get_office_color_keyboard(),
        state_for_dedupe=OrderStates.OFFICE_COLOR,
        context=context,
    )

async def render_common_files_office(update, context):
    from keyboards import get_files_keyboard
    await say(
        update,
        "📎 Загрузите макет (PDF/JPG/PNG). Затем нажмите «➡️ Далее».",
        reply_markup=get_files_keyboard(),
        state_for_dedupe=OrderStates.ORDER_FILES,
        context=context,
    )

# -------- ПЛАКАТЫ --------
async def render_poster_format(update, context):
    from keyboards import get_poster_format_keyboard
    await say(
        update,
        "📐 Выберите формат плаката:",
        reply_markup=get_poster_format_keyboard(),
        state_for_dedupe=OrderStates.POSTER_FORMAT,
        context=context,
    )

async def render_poster_lamination(update, context):
    from keyboards import get_simple_lamination_keyboard
    await say(
        update,
        "✨ Ламинация плаката:",
        reply_markup=get_simple_lamination_keyboard(),
        state_for_dedupe=OrderStates.ORDER_POSTPRESS,
        context=context,
    )

# -------- ФЛАЕРЫ --------
async def render_flyer_quantity(update, context):
    from keyboards import nav_keyboard
    await say(
        update,
        "📊 Укажите количество флаеров:",
        reply_markup=nav_keyboard(),
        state_for_dedupe=OrderStates.QUANTITY,
        context=context,
    )

async def render_flyer_format(update, context):
    from keyboards import get_fly_format_keyboard
    await say(
        update,
        "📐 Формат флаеров:",
        reply_markup=get_fly_format_keyboard(),
        state_for_dedupe=OrderStates.FLY_FORMAT,
        context=context,
    )

async def render_flyer_sides(update, context):
    from keyboards import get_fly_sides_keyboard
    await say(
        update,
        "🖨️ Стороны печати флаеров:",
        reply_markup=get_fly_sides_keyboard(),
        state_for_dedupe=OrderStates.FLY_SIDES,
        context=context,
    )

# -------- НАКЛЕЙКИ --------
async def render_sticker_quantity(update, context):
    from keyboards import nav_keyboard
    await say(
        update,
        "📊 Укажите количество наклеек:",
        reply_markup=nav_keyboard(),
        state_for_dedupe=OrderStates.QUANTITY,
        context=context,
    )

async def render_sticker_size(update, context):
    from keyboards import get_files_keyboard
    await say(
        update,
        "📏 Укажите размер наклеек:",
        reply_markup=get_files_keyboard(),
        state_for_dedupe=OrderStates.STICKER_SIZE,
        context=context,
    )

async def render_sticker_material(update, context):
    from keyboards import get_sticker_material_keyboard
    await say(
        update,
        "📄 Материал наклеек:",
        reply_markup=get_sticker_material_keyboard(),
        state_for_dedupe=OrderStates.STICKER_MATERIAL,
        context=context,
    )

async def render_sticker_color(update, context):
    from keyboards import get_sticker_color_keyboard
    await say(
        update,
        "🎨 Цветность наклеек:",
        reply_markup=get_sticker_color_keyboard(),
        state_for_dedupe=OrderStates.STICKER_COLOR,
        context=context,
    )

# -------- ОБЩИЕ ШАГИ --------
async def render_phone(update, context):
    from keyboards import get_phone_keyboard
    await say(
        update,
        "📞 Укажите телефон для связи:",
        reply_markup=get_phone_keyboard(),
        state_for_dedupe=OrderStates.PHONE,
        context=context,
    )

async def render_notes(update, context):
    from keyboards import get_notes_keyboard
    await say(
        update,
        "📝 Дополнительные пожелания (необязательно):",
        reply_markup=get_notes_keyboard(),
        state_for_dedupe=OrderStates.NOTES,
        context=context,
    )

async def render_due(update, context):
    from keyboards import get_due_keyboard
    await say(
        update,
        "📅 Укажите желаемый срок выполнения (например: завтра, 05.10.2025 14:00) или нажмите «⏭️ Пропустить»:",
        reply_markup=get_due_keyboard(),
        state_for_dedupe=OrderStates.ORDER_DUE,
        context=context,
    )

async def render_confirm(update, context):
    from keyboards import get_confirm_keyboard
    summary = format_order_summary(context.user_data)
    await say(
        update,
        f"{texts.CONFIRM_PROMPT}\n\n{summary}",
        reply_markup=get_confirm_keyboard(),
        state_for_dedupe=OrderStates.CONFIRM,
        context=context,
    )


async def render_state(update, context, state):
    """Отрисовать переданный шаг с его родной клавиатурой (без изменения данных)."""
    # если пришло из callback — погасим «часики» и очистим инлайн-клавиатуру
    if getattr(update, "callback_query", None):
        try:
            await update.callback_query.answer()
        except Exception:
            pass
    fn = STATE_RENDERERS.get(state)
    if fn is None:
        # запасной вариант — вернёмся к категориям
        await render_choose_category(update, context)
        return OrderStates.CHOOSE_CATEGORY
    await fn(update, context)
    return state

from keyboards import (
    get_category_keyboard,
    get_categories_keyboard,
    get_office_format_keyboard,
    get_office_color_keyboard,
    get_poster_format_keyboard,
    get_simple_lamination_keyboard,
    get_bc_format_keyboard,
    get_bc_sides_keyboard,
    get_bc_lamination_keyboard,
    get_fly_format_keyboard,
    get_fly_sides_keyboard,
    get_sticker_material_keyboard,
    get_sticker_color_keyboard,
    get_files_keyboard,
    get_due_keyboard,
    get_phone_keyboard,
    get_notes_keyboard,
    get_confirm_keyboard,
    get_main_menu_keyboard,
    get_cancel_choice_keyboard,
    nav_keyboard,
    BTN_NEXT,
    BTN_CANCEL,
    BTN_CANCEL_ORDER,
    BTN_SKIP,
    CAT_BC,
    CAT_POSTERS,
    CAT_FLYERS,
    CAT_STICKERS,
    CAT_BANNERS,
    CAT_OFFICE,
    BTN_CUSTOM,
)
from handlers.common import main_menu_keyboard
from services.notifier import send_order_to_operators
from services.validators import parse_due, validate_phone, normalize_phone, validate_bc_quantity, validate_quantity, parse_exemplars
from services.formatting import format_order_summary
from services.orders import create_order
import config
import texts

logger = logging.getLogger(__name__)

CANCEL_RE = r"^(?:❌ Отмена|Отмена|/cancel)$"
BACK_RE   = r"^(?:↩️ Назад|Назад|/back)$"
SKIP_RE   = r"^(?:⏭️ Пропустить|Пропустить)$"

# Тексты для разных этапов
ASK_OFFICE_FORMAT = "📄 Выберите формат офисной бумаги:"
ASK_OFFICE_COLOR = "🎨 Выберите цветность печати:"
ASK_POSTER_FORMAT = "📐 Выберите формат плаката:"
ASK_POSTER_POSTPRESS = "✨ Ламинация плаката:"


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================


# ==================== НАЧАЛО ЗАКАЗА ====================

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало оформления заказа"""
    context.user_data.clear()                 # полный сброс
    context.user_data["state_stack"] = []     # новый стек
    return await goto(update, context, OrderStates.CHOOSE_CATEGORY, render_choose_category)


# ==================== ВЫБОР КАТЕГОРИИ ====================

async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора категории печати"""
    from handlers.common import start_command
    text = (update.message.text or "").strip()
    # Дублирующая защита: если вдруг это "Назад" — уводим в /start
    if text.lower().endswith("назад"):
        return await start_command(update, context)
    
    # Индивидуальный заказ
    if text == BTN_CUSTOM:
        from keyboards import add_contact_row, InlineKeyboardMarkup
        from texts import CONTACTS_TEXT
        
        # Создаем инлайн-клавиатуру с кнопкой контактов
        rows = []
        rows = add_contact_row(rows)
        keyboard = InlineKeyboardMarkup(rows)
        
        await say(
            update,
            (
                "🛠️ *Индивидуальный заказ*\n\n"
                "Хотите что-то особенное — нестандартный формат, материал или "
                "индивидуальный дизайн? Мы с радостью подготовим для вас персональное предложение 🙌\n\n"
                f"{CONTACTS_TEXT}\n\n"
                "Он уточнит детали и поможет оформить заказ."
            ),
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        return ConversationHandler.END
    
    # Визитки
    elif text == CAT_BC:
        context.user_data["what_to_print"] = "Визитки"
        context.user_data["category"] = "business_card"
        return await goto(update, context, OrderStates.BC_QTY, render_bc_qty)
    
    # Плакаты
    elif text == CAT_POSTERS:
        context.user_data["what_to_print"] = "Плакаты"
        context.user_data["category"] = "poster"
        return await goto(update, context, OrderStates.POSTER_FORMAT, render_poster_format)
    
    # Флаеры
    elif text == CAT_FLYERS:
        context.user_data["what_to_print"] = "Флаеры"
        context.user_data["category"] = "flyer"
        return await goto(update, context, OrderStates.QUANTITY, render_flyer_quantity)
    
    # Наклейки
    elif text == CAT_STICKERS:
        context.user_data["what_to_print"] = "Наклейки"
        context.user_data["category"] = "sticker"
        return await goto(update, context, OrderStates.QUANTITY, render_sticker_quantity)
    
    # Баннеры - редирект к оператору
    elif text == CAT_BANNERS:
        from keyboards import add_contact_row, InlineKeyboardMarkup
        from texts import CONTACTS_TEXT
        
        # Создаем инлайн-клавиатуру с кнопкой контактов
        rows = []
        rows = add_contact_row(rows)
        keyboard = InlineKeyboardMarkup(rows)
        
        # инфо-карточка → назад в категории
        await say(update,
            "🖼️ Баннеры сейчас оформляются через оператора.\n"
            "Напишите, пожалуйста, — мы быстро всё уточним и оформим.\n\n"
            f"{CONTACTS_TEXT}",
            reply_markup=keyboard,
            state_for_dedupe=OrderStates.CHOOSE_CATEGORY, context=context
        )
        return await goto(update, context, OrderStates.CHOOSE_CATEGORY, render_choose_category)
    
    # Офисная бумага
    elif text == CAT_OFFICE:
        context.user_data["what_to_print"] = "Печать на офисной бумаге"
        context.user_data["category"] = "office"
        return await goto(update, context, OrderStates.QUANTITY, render_office_copies)
    
    # не распознали — просто заново категории
    return await goto(update, context, OrderStates.CHOOSE_CATEGORY, render_choose_category)


# ==================== КОЛИЧЕСТВО ====================

def _parse_int_positive(txt):
    try:
        n=int(str(txt).strip())
        return n if n>0 else None
    except: return None

async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода количества"""
    text = (update.message.text or "").strip()
    
    qty = _parse_int_positive(text)
    if not qty:
        await say(update, "❌ Введите целое число больше 0.", state_for_dedupe=OrderStates.QUANTITY, context=context)
        return await goto(update, context, OrderStates.QUANTITY, render_office_copies)
    
    context.user_data["quantity"] = qty
    
    # Переход в зависимости от категории
    category = context.user_data.get("category", "")
    
    if category == "flyer":
        return await goto(update, context, OrderStates.FLY_FORMAT, render_flyer_format)
    
    elif category == "sticker":
        return await goto(update, context, OrderStates.STICKER_SIZE, render_sticker_size)
    
    elif category == "office":
        # Парсинг количества экземпляров
        text = (update.message.text or "").strip()
        qty = parse_exemplars(text)
        if not qty:
            await say(update, "❌ Не понял количество. Введите число (например, 3) или словами (например, «три»).", state_for_dedupe=OrderStates.QUANTITY, context=context)
            return await goto(update, context, OrderStates.QUANTITY, render_office_copies)
        context.user_data["quantity"] = qty
        
        return await goto(update, context, OrderStates.OFFICE_FORMAT, render_office_format)
    
    else:
        return await render_state(update, context, OrderStates.ORDER_FILES)


async def handle_bc_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка тиража визиток (кратно 50)"""
    text = (update.message.text or "").strip()
    
    try:
        qty = int(text)
        if not validate_bc_quantity(qty):
            await say(update, texts.ERR_BC_STEP, state_for_dedupe=OrderStates.BC_QTY, context=context)
            return await goto(update, context, OrderStates.BC_QTY, render_bc_qty)
        
        context.user_data["quantity"] = qty
        return await goto(update, context, OrderStates.BC_FORMAT, render_bc_format)
    
    except ValueError:
        await say(update, texts.ERR_INT, state_for_dedupe=OrderStates.BC_QTY, context=context)
        return await goto(update, context, OrderStates.BC_QTY, render_bc_qty)


# ==================== ОФИСНАЯ БУМАГА ====================

async def handle_office_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка формата офисной бумаги"""
    text = (update.message.text or "").strip().upper()
    if text not in {"A4", "A3"}:
        await say(update, "Пожалуйста, выберите формат: A4 или A3.", reply_markup=get_office_format_keyboard(), state_for_dedupe=OrderStates.OFFICE_FORMAT, context=context)
        return await goto(update, context, OrderStates.OFFICE_FORMAT, render_office_format)

    context.user_data["format"] = text
    context.user_data["sheet_format"] = text
    return await goto(update, context, OrderStates.OFFICE_COLOR, render_office_color)


async def handle_office_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка цветности офисной бумаги"""
    text = (update.message.text or "").strip().lower()
    if text not in {"ч/б", "⚫ ч/б", "цветная", "🌈 цветная"}:
        await say(update, "Выберите: ⚫ Ч/Б или 🌈 Цветная.", reply_markup=get_office_color_keyboard(), state_for_dedupe=OrderStates.OFFICE_COLOR, context=context)
        return await goto(update, context, OrderStates.OFFICE_COLOR, render_office_color)

    color = "bw" if "ч/б" in text else "color"
    context.user_data["print_color"] = color
    context.user_data["lamination"] = "none"
    context.user_data["quantity"] = context.user_data.get("quantity", 1)
    
    # Переход на загрузку PDF
    return await render_state(update, context, OrderStates.ORDER_FILES)


# ==================== ПЛАКАТЫ ====================

async def handle_poster_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка формата плаката"""
    text = (update.message.text or "").strip().upper()
    if text not in {"A2", "A1", "A0"}:
        await say(update, "Пожалуйста, выберите формат: A2, A1 или A0.", reply_markup=get_poster_format_keyboard(), state_for_dedupe=OrderStates.POSTER_FORMAT, context=context)
        return await goto(update, context, OrderStates.POSTER_FORMAT, render_poster_format)

    context.user_data["format"] = text
    context.user_data["sheet_format"] = text
    context.user_data["quantity"] = context.user_data.get("quantity", 1)
    
    return await goto(update, context, OrderStates.ORDER_POSTPRESS, render_poster_lamination)


async def handle_poster_lamination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ламинации плаката"""
    text = (update.message.text or "").strip().lower()
    if text not in {"ламинация: да", "ламинация: нет", "да", "нет"}:
        await say(update, "Выберите: Ламинация: Да / Ламинация: Нет", reply_markup=get_simple_lamination_keyboard(), state_for_dedupe=OrderStates.ORDER_POSTPRESS, context=context)
        return await goto(update, context, OrderStates.ORDER_POSTPRESS, render_poster_lamination)

    lamination = "glossy" if "да" in text else "none"
    context.user_data["lamination"] = lamination
    context.user_data["print_color"] = "color"
    
    return await render_state(update, context, OrderStates.ORDER_FILES)


# ==================== ВИЗИТКИ ====================

async def handle_bc_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка формата визиток"""
    text = (update.message.text or "").strip()
    
    # Принимаем любой текст, т.к. формат один
    context.user_data["format"] = "90×50 мм"
    context.user_data["sheet_format"] = "90x50"
    
    return await goto(update, context, OrderStates.BC_SIDES, render_bc_sides)


async def handle_bc_sides(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сторонности визиток"""
    text = (update.message.text or "").strip().lower()
    
    if "двусторонн" in text:
        sides = "2"
    elif "односторонн" in text:
        sides = "1"
    else:
        await say(update, "Выберите: Односторонние или Двусторонние", reply_markup=get_bc_sides_keyboard(), state_for_dedupe=OrderStates.BC_SIDES, context=context)
        return await goto(update, context, OrderStates.BC_SIDES, render_bc_sides)
    
    context.user_data["sides"] = sides
    return await goto(update, context, OrderStates.BC_LAMINATION, render_bc_lamination)


async def handle_bc_lamination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ламинации визиток"""
    text = (update.message.text or "").strip().lower()
    
    if "матов" in text:
        lamination = "matte"
    elif "глянец" in text or "глянц" in text:
        lamination = "glossy"
    elif "нет" in text or "❌" in text:
        lamination = "none"
    else:
        await say(update, "Выберите: ✨ Матовая, ✨ Глянец или ❌ Нет", reply_markup=get_bc_lamination_keyboard(), state_for_dedupe=OrderStates.BC_LAMINATION, context=context)
        return await goto(update, context, OrderStates.BC_LAMINATION, render_bc_lamination)
    
    context.user_data["lamination"] = lamination
    context.user_data["print_color"] = "color"
    context.user_data["bigovka_count"] = 0  # Без биговки
    
    return await render_state(update, context, OrderStates.ORDER_FILES)


# ==================== ФЛАЕРЫ ====================

async def handle_fly_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка формата флаера"""
    text = (update.message.text or "").strip().upper()
    
    if text not in {"A7", "A6", "A5", "A4"}:
        await say(update, "Выберите формат: A7, A6, A5 или A4", reply_markup=get_fly_format_keyboard(), state_for_dedupe=OrderStates.FLY_FORMAT, context=context)
        return await goto(update, context, OrderStates.FLY_FORMAT, render_flyer_format)
    
    context.user_data["format"] = text
    context.user_data["sheet_format"] = text
    
    return await goto(update, context, OrderStates.FLY_SIDES, render_flyer_sides)


async def handle_fly_sides(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сторонности флаера"""
    text = (update.message.text or "").strip().lower()
    
    if "двусторонн" in text:
        sides = "2"
    elif "односторонн" in text:
        sides = "1"
    else:
        await say(update, "Выберите: Односторонние или Двусторонние", reply_markup=get_fly_sides_keyboard(), state_for_dedupe=OrderStates.FLY_SIDES, context=context)
        return await goto(update, context, OrderStates.FLY_SIDES, render_flyer_sides)
    
    context.user_data["sides"] = sides
    context.user_data["lamination"] = "none"
    context.user_data["print_color"] = "color"
    
    return await render_state(update, context, OrderStates.ORDER_FILES)


# ==================== НАКЛЕЙКИ ====================

async def handle_sticker_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка размера наклеек"""
    text = (update.message.text or "").strip()
    
    # Принимаем любой текст как размер
    context.user_data["format"] = text
    context.user_data["custom_size_mm"] = text
    
    return await goto(update, context, OrderStates.STICKER_MATERIAL, render_sticker_material)


async def handle_sticker_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка материала наклеек"""
    text = (update.message.text or "").strip().lower()
    
    if "бумага" in text:
        material = "paper"
    elif "пленк" in text or "винил" in text:
        material = "vinyl"
    else:
        await say(update, "Выберите: Бумага или Пленка", reply_markup=get_sticker_material_keyboard(), state_for_dedupe=OrderStates.STICKER_MATERIAL, context=context)
        return await goto(update, context, OrderStates.STICKER_MATERIAL, render_sticker_material)
    
    context.user_data["material"] = material
    
    return await goto(update, context, OrderStates.STICKER_COLOR, render_sticker_color)


async def handle_sticker_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка цветности наклеек"""
    text = (update.message.text or "").strip().lower()
    
    if "ч/б" in text or "черно-бел" in text:
        color = "bw"
    elif "цвет" in text:
        color = "color"
    else:
        await say(update, "Выберите: ⚫ Ч/Б или 🌈 Цветная", reply_markup=get_sticker_color_keyboard(), state_for_dedupe=OrderStates.STICKER_COLOR, context=context)
        return await goto(update, context, OrderStates.STICKER_COLOR, render_sticker_color)
    
    context.user_data["print_color"] = color
    context.user_data["lamination"] = "none"
    
    return await render_state(update, context, OrderStates.ORDER_FILES)


# ==================== ЗАГРУЗКА ФАЙЛОВ ====================

# ✅ Универсальный обработчик загрузки файлов
async def handle_file(update, context):
    ud = context.user_data
    files = ud.setdefault("files", [])

    # Документ
    if update.message.document:
        doc = update.message.document
        ext = _get_ext(doc.file_name)
        files.append({"type": "document", "ext": ext})

    # Фото
    elif update.message.photo:
        files.append({"type": "photo", "ext": "jpg"})

    await say(update, "✅ Файл получен.", state_for_dedupe=OrderStates.ORDER_FILES, context=context)

async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка загрузки файлов"""
    
    # Если нажата кнопка "Далее"
    if (update.message and update.message.text == BTN_NEXT):
        product = context.user_data.get("category")  # 'business_card', 'poster', 'flyer', 'sticker', 'office'
        files = context.user_data.get("files", [])

        if not files:
            await say(update, "❌ Загрузите хотя бы один файл (PDF/JPG/PNG).", state_for_dedupe=OrderStates.ORDER_FILES, context=context)
            return await goto(update, context, OrderStates.ORDER_FILES, render_common_files)

        if product == "business_card":  # визитки — только PDF
            if not all(f["ext"] == "pdf" for f in files):
                await say(update, "❌ Для визиток допускается только PDF-файл. Загрузите PDF и затем нажмите «➡️ Далее».", state_for_dedupe=OrderStates.ORDER_FILES, context=context)
                return await goto(update, context, OrderStates.ORDER_FILES, render_common_files)
        else:
            for f in files:
                if f["ext"] not in ALLOWED_COMMON_EXTS:
                    await say(update, "❌ Загрузите файл в формате PDF, JPG или PNG.", state_for_dedupe=OrderStates.ORDER_FILES, context=context)
                    return await goto(update, context, OrderStates.ORDER_FILES, render_common_files)

        # Всё ок — переход на следующий шаг
        return await goto(update, context, OrderStates.PHONE, render_phone)
    
    # Обработка загрузки файлов
    if update.message.document or update.message.photo:
        return await handle_file(update, context)
    


# ==================== СРОК ====================

async def handle_due(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка срока выполнения"""
    text = (update.message.text or "").strip()
    
    # Обработка кнопки "Пропустить"
    if update.message.text == BTN_SKIP:
        context.user_data["deadline_at"] = None
        context.user_data.setdefault("notes", []).append(
            "После проверки макета менеджер сориентирует по срокам и стоимости."
        )
        return await render_state(update, context, OrderStates.PHONE)
    
    if re.match(SKIP_RE, text, flags=re.I) or "после проверки" in text.lower():
        context.user_data["deadline_at"] = None
        context.user_data.setdefault("notes", []).append(
            "После проверки макета менеджер сориентирует по срокам и стоимости."
        )
        return await render_state(update, context, OrderStates.PHONE)

    due = parse_due(text, tz="Europe/Moscow")  # или из config
    if not due:
        await say(update, "❌ Не смог понять срок. Примеры: завтра, 05.10.2025 14:00.\nИли нажмите «⏭️ Пропустить».", state_for_dedupe=OrderStates.ORDER_DUE, context=context)
        return await goto(update, context, OrderStates.ORDER_DUE, render_due)

    context.user_data["deadline_at"] = due
    context.user_data["deadline_note"] = None
    return await render_state(update, context, OrderStates.PHONE)


# ==================== ТЕЛЕФОН ====================

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка номера телефона"""
    text = (update.message.text or "").strip()
    
    phone = normalize_phone(text)
    if not phone:
        await say(update, "❌ Введите корректный телефон. Пример: +7 999 123-45-67", state_for_dedupe=OrderStates.PHONE, context=context)
        return await goto(update, context, OrderStates.PHONE, render_phone)

    # сохранить в заказ и идти дальше как раньше
    context.user_data["contact"] = phone
    return await goto(update, context, OrderStates.NOTES, render_notes)


# ==================== ПОЖЕЛАНИЯ ====================

async def handle_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка дополнительных пожеланий"""
    text = (update.message.text or "").strip()
    
    # Если нажата кнопка "Пропустить"
    if "пропустить" in text.lower() or "⏭️" in text:
        context.user_data["notes"] = ""
    else:
        context.user_data["notes"] = text
    
    return await goto(update, context, OrderStates.CONFIRM, render_confirm)


# ==================== ПОДТВЕРЖДЕНИЕ ====================

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения заказа"""
    text = (update.message.text or "").strip().lower()
    
    if "подтвердить" in text or "✅" in text:
        try:
            # Создаем заказ в БД
            user = update.effective_user
            order = create_order(context.user_data, user.id)
            
            # Уведомляем операторов, но не роняем сценарий, если чаты не найдены
            try:
                results = await send_order_to_operators(
                    context.bot,
                    order,
                    user,
                    config.config.OPERATOR_CHAT_ID,
                    order.code
                )
                # для дебага можно коротко логнуть сводку
                ok = sum(1 for _, s, _ in results if s)
                fail = sum(1 for _, s, _ in results if not s)
                logger.info(f"Operator notify summary: ok={ok} fail={fail}")
            except Exception as e:
                # На всякий случай — жесткая изоляция ошибок
                logger.exception(f"Operator notify crashed: {e}")
                # не сообщаем пользователю про "тех. ошибку"
            
            # Уведомляем клиента финальным сообщением
            from keyboards import get_main_menu_keyboard
            await update.message.reply_text(
                texts.ORDER_ACCEPTED,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown"
            )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except Exception as e:
            logger.exception("Error creating order: %s", e)
            await update.message.reply_text(
                texts.TECH_ERROR,
                reply_markup=main_menu_keyboard()
            )
            context.user_data.clear()
            return ConversationHandler.END
    
    elif "изменить" in text or "✏️" in text:
        await update.message.reply_text(
            "Начните заново с команды /neworder",
            reply_markup=main_menu_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    else:
        await say(update, "Выберите: ✅ Подтвердить или ✏️ Изменить", reply_markup=get_confirm_keyboard(), state_for_dedupe=OrderStates.CONFIRM, context=context)
        return await goto(update, context, OrderStates.CONFIRM, render_confirm)


# ==================== НАВИГАЦИЯ ====================

async def handle_back(update, context):
    pop_state(context)             # убрать текущий
    prev = top_state(context)      # взять предыдущий
    if prev is None:
        # если стека нет — стартовое меню
        from handlers.common import start_command
        context.user_data.pop("last_screen_fp", None)
        await start_command(update, context)
        return ConversationHandler.END

    context.user_data.pop("last_screen_fp", None)
    return await render_state(update, context, prev)


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Умная отмена"""
    from keyboards import smart_cancel_inline
    return await say(update, "Что именно отменить?", reply_markup=smart_cancel_inline())

async def handle_cancel_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор в подтверждении отмены"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "cancel_step":
        # Отмена шага → Назад
        return await handle_back(update, context)

    if data == "cancel_all":
        context.user_data.clear()
        await context.bot.send_message(
            update.effective_chat.id,
            "Отменено."
        )
        from handlers.common import start_command
        return await start_command(update, context)


# === Спец-обработчик «⬅️ Назад» на экране выбора категории ===
def _top_state(ctx):
    stack = ctx.user_data.get("state_stack") or []
    return stack[-1] if stack else None

async def handle_back_from_categories(update, context):
    """
    На экране выбора категории: '⬅️ Назад' ведет в /start.
    """
    if _top_state(context) != OrderStates.CHOOSE_CATEGORY:
        # на других шагах не трогаем
        return _top_state(context) or OrderStates.CHOOSE_CATEGORY

    context.user_data.clear()
    from handlers.common import start_command
    await start_command(update, context)
    return ConversationHandler.END


# СЛОВАРЬ «СОСТОЯНИЕ → ФУНКЦИЯ ОТРИСОВКИ»
STATE_RENDERERS = {
    OrderStates.CHOOSE_CATEGORY: render_choose_category,

    # Визитки
    OrderStates.BC_QTY:           render_bc_qty,
    OrderStates.BC_FORMAT:        render_bc_format,
    OrderStates.BC_SIDES:         render_bc_sides,
    OrderStates.BC_LAMINATION:    render_bc_lamination,
    OrderStates.ORDER_FILES:      render_common_files,  # общий для всех категорий

    # Офисная печать
    OrderStates.QUANTITY:         render_office_copies,  # для офисной печати
    OrderStates.OFFICE_FORMAT:    render_office_format,
    OrderStates.OFFICE_COLOR:     render_office_color,

    # Плакаты
    OrderStates.POSTER_FORMAT:    render_poster_format,
    OrderStates.ORDER_POSTPRESS:  render_poster_lamination,

    # Флаеры
    OrderStates.FLY_FORMAT:       render_flyer_format,
    OrderStates.FLY_SIDES:        render_flyer_sides,

    # Наклейки
    OrderStates.STICKER_SIZE:     render_sticker_size,
    OrderStates.STICKER_MATERIAL: render_sticker_material,
    OrderStates.STICKER_COLOR:    render_sticker_color,

    # Общие шаги
    OrderStates.ORDER_DUE:        render_due,
    OrderStates.PHONE:            render_phone,
    OrderStates.NOTES:            render_notes,
    OrderStates.CONFIRM:          render_confirm,
}

# Защита на случай, если кто-то забудет импортировать OrderStates
if 'OrderStates' not in globals():
    from states import OrderStates

# handlers/order_flow.py
from telegram.ext import ConversationHandler

async def reset_to_start(update, context):
    """Завершить любой текущий диалог и показать главное меню."""
    try:
        context.user_data.clear()
    except Exception:
        pass
    # сброс локального стека, если используем
    try:
        context.user_data["state_stack"] = []
    except Exception:
        pass

    from handlers.common import start_command
    await start_command(update, context)
    return ConversationHandler.END


async def unknown_command_during_flow(update, context):
    """Мягко сообщаем, что команда недоступна во время оформления."""
    try:
        from keyboards import nav_keyboard
        await update.effective_message.reply_text(
            "Команда недоступна во время оформления заказа. "
            "Пожалуйста, используйте кнопки ниже.",
            reply_markup=nav_keyboard() if 'nav_keyboard' in globals() else None
        )
    except Exception:
        await update.effective_message.reply_text("⚠️ Техническая ошибка. Попробуйте ещё раз.")

    # остаёмся на текущем шаге, если он известен
    st = context.user_data.get("state_stack", [])
    try:
        from states import OrderStates
        return st[-1] if st else OrderStates.CHOOSE_CATEGORY
    except Exception:
        return ConversationHandler.END
