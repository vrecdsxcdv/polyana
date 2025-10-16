# keyboards.py
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

BTN_BACK   = "⬅️ Назад"
BTN_NEXT   = "➡️ Далее"
BTN_SKIP   = "⏭️ Пропустить"
BTN_CANCEL = "❌ Отмена"
BTN_CANCEL_ORDER = "🛑 Отменить заказ"

# Константы для fallbacks
NAV_BACK = "↩️ Назад"
NAV_CANCEL = "❌ Отмена"

BTN_NEW_ORDER = "🧾 Новый заказ"
BTN_MY_ORDERS = "📦 Мои заказы"
BTN_CALL_OPERATOR = "🧑‍💼 Связаться с оператором"
BTN_HELP = "🆘 Помощь"

# Тексты категорий
CAT_BC       = "🪪 Визитки"
CAT_POSTERS  = "🖼 Плакаты"
CAT_FLYERS   = "📄 Флаеры"
CAT_STICKERS = "🏷️ Наклейки"
CAT_BANNERS  = "🖨 Баннеры"
CAT_OFFICE   = "🗂 Печать на офисной"
BTN_CUSTOM   = "🛠️ Индивидуальный заказ"

def bottom_row():
    return [BTN_BACK, BTN_CANCEL]

def get_main_menu_keyboard():
    # Этаж 1 — Новый заказ (во всю ширину)
    # Этаж 2 — пополам Мои заказы / Связаться с оператором
    # Этаж 3 — Помощь (во всю ширину)
    return ReplyKeyboardMarkup(
        [
            [BTN_NEW_ORDER],
            [BTN_MY_ORDERS, BTN_CALL_OPERATOR],
            [BTN_HELP],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

def get_categories_keyboard():
    """
    Клавиатура выбора категории ('Что будем печатать?')
    Без кнопки 'Отмена', с кнопкой '⬅️ Назад', которая ведет в главное меню.
    """
    rows = [
        [CAT_BC, CAT_POSTERS],
        [CAT_FLYERS, CAT_STICKERS],
        [CAT_BANNERS, CAT_OFFICE],
        [BTN_CUSTOM],
        [BTN_BACK],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)

# Алиас для совместимости
get_category_keyboard = get_categories_keyboard

def get_cancel_choice_keyboard():
    return ReplyKeyboardMarkup(
        [["↩️ Отменить этот шаг", "🗑️ Отменить весь заказ"],
         [BTN_BACK]],
        resize_keyboard=True, is_persistent=True
    )

# Хелпер: нижняя навигация для шагов (Назад/Отмена + опционально Далее/Пропустить)
def nav_keyboard(show_next=False, show_skip=False):
    row = [BTN_BACK, BTN_CANCEL]
    rows = [row]
    if show_next or show_skip:
        extra = []
        if show_next: extra.append(BTN_NEXT)
        if show_skip: extra.append(BTN_SKIP)
        rows.append(extra)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)

# Алиас на случай старого кода (будет определен после get_bc_sides_keyboard)

# Офисная бумага
def get_office_format_keyboard():
    return ReplyKeyboardMarkup(
        [["A4", "A3"], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

def get_office_color_keyboard():
    return ReplyKeyboardMarkup(
        [["⚫ Ч/Б", "🌈 Цветная"], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

# Плакаты
def get_poster_format_keyboard():
    return ReplyKeyboardMarkup(
        [["A2", "A1", "A0"], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

def get_simple_lamination_keyboard():
    return ReplyKeyboardMarkup(
        [["Ламинация: Да", "Ламинация: Нет"], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

# Визитки
def get_bc_format_keyboard():
    return ReplyKeyboardMarkup(
        [["90×50 мм"], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

def get_bc_sides_keyboard():
    return ReplyKeyboardMarkup(
        [["Односторонние", "Двусторонние"], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

def get_bc_lamination_keyboard():
    return ReplyKeyboardMarkup(
        [["✨ Матовая", "✨ Глянец", "❌ Нет"], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

# Флаеры
def get_fly_format_keyboard():
    return ReplyKeyboardMarkup(
        [["A7", "A6"], ["A5", "A4"], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

def get_fly_sides_keyboard():
    return ReplyKeyboardMarkup(
        [["Односторонние", "Двусторонние"], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

# Наклейки
def get_sticker_material_keyboard():
    return ReplyKeyboardMarkup(
        [["Бумага", "Пленка"], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

def get_sticker_color_keyboard():
    return ReplyKeyboardMarkup(
        [["⚫ Ч/Б", "🌈 Цветная"], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

# Общие клавиатуры
def get_files_keyboard():
    return ReplyKeyboardMarkup(
        [[BTN_NEXT], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

def get_due_keyboard():
    return ReplyKeyboardMarkup(
        [[BTN_SKIP], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

def get_phone_keyboard():
    return ReplyKeyboardMarkup(
        [bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

def get_notes_keyboard():
    return ReplyKeyboardMarkup(
        [[BTN_SKIP], bottom_row()],
        resize_keyboard=True,
        is_persistent=True,
    )

def get_confirm_keyboard():
    return ReplyKeyboardMarkup(
        [["✅ Подтвердить", "✏️ Изменить"], [BTN_CANCEL]],
        resize_keyboard=True,
        is_persistent=True,
    )

# Алиас на случай старого кода
get_fly_sides_keyboard = get_bc_sides_keyboard

def smart_cancel_inline():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Отменить этот шаг", callback_data="cancel_step")],
        [InlineKeyboardButton("✖️ Отменить заказ",   callback_data="cancel_all")],
    ])

# Inline клавиатура для списка заказов (2-3 в ряд)
def make_orders_inline_kb(orders):
    """
    Генерит InlineKeyboardMarkup со списком заказов.
    Кнопка = номер заказа, callback_data = "order_view:<CODE>"
    """
    buttons = []
    row = []
    for i, o in enumerate(orders, start=1):
        code = getattr(o, "code", None)
        if not code:
            continue
        row.append(InlineKeyboardButton(text=f"#{code}", callback_data=f"order_view:{code}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons) if buttons else None
