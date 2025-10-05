"""
Клавиатуры для бота типографии.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from services.callbacks import OP_TAKE, OP_READY, OP_NEEDS_FIX, OP_CONTACT, make_cb
from services.callbacks import CANCEL_YES, CANCEL_NO

# Константы для кнопок (единый источник правды)
BTN_NEW_ORDER = "📝 Новый заказ"
BTN_MY_ORDERS = "📊 Мои заказы"
BTN_SUPPORT = "👨‍💬 Позвать оператора"
BTN_HELP = "❓ Помощь"
BTN_BACK = "⬅️ Назад"
BTN_CANCEL = "❌ Отмена"
BTN_NEXT = "➡️ Далее"
BTN_SKIP = "⏭️ Пропустить"
BTN_SUBMIT = "Готово"

BTN_BC = "Визитки"
BTN_FLY = "Флаеры"
BTN_BNR = "Баннеры"
BTN_PLK = "Плакаты"
BTN_STK = "Наклейки"
BTN_OTHER = "Другое"
BTN_1 = "Односторонняя"
BTN_2 = "Двусторонняя"
BTN_BC_SIZE = "Визитка 90×50"
BTN_LOAD_MORE = "Показать ещё…"

# Типы печати
PRINT_TYPES = ["Визитки", "Флаеры", "Баннеры", "Плакаты", "Наклейки", "Другое"]

# Алиасы для нормализации ввода
ALIAS = {
    "двусторонняя": "2-sided",
    "2-сторонняя": "2-sided", 
    "2 sided": "2-sided",
    "двусторонняя печать": "2-sided",
    "односторонняя": "1-sided",
    "1 sided": "1-sided",
    "односторонняя печать": "1-sided",
    "цветная": "4+4",
    "цветная печать": "4+4",
    "ч/б": "1+0",
    "черно-белая": "1+0",
    "черно белая": "1+0",
    "да": "yes",
    "нет": "no",
    "есть": "yes",
    "есть макет": "yes",
    "нет макета": "no",
    "дизайнер": "designer",
    "нужен дизайнер": "designer",
    "нужен": "designer"
}

def norm(text: str) -> str:
    """Нормализует текст для сравнения."""
    return (text or "").strip().casefold()

def alias_map(s: str) -> str:
    """Применяет алиасы к тексту."""
    s2 = norm(s)
    return ALIAS.get(s2, s)


def get_keyboard_remove() -> ReplyKeyboardRemove:
    """Удаляет клавиатуру для сброса кеша."""
    return ReplyKeyboardRemove()

def get_home_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота."""
    return ReplyKeyboardMarkup(
        [
            ["🆕 Новый заказ"],                       # крупная верхняя
            ["📦 Мои заказы", "☎️ Связаться с оператором"],          # нижний ряд
            ["❓ Помощь"],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def get_product_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора продукта."""
    return ReplyKeyboardMarkup([
        ["🪪 Визитки", "📄 Флаеры"],
        ["🖼 Баннеры", "📰 Плакаты"],
        ["🏷 Наклейки", "📚 Листы"],
        ["📦 Другое"],
        ["⬅️ Назад", "❌ Отмена"]
    ], resize_keyboard=True, is_persistent=True)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота (для совместимости)."""
    return get_home_keyboard()


def get_navigation_keyboard(show_skip: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура навигации (Назад, Отмена)."""
    buttons = [
        [InlineKeyboardButton(BTN_BACK, callback_data="back")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data="cancel")]
    ]
    
    if show_skip:
        buttons.insert(-1, [InlineKeyboardButton(BTN_SKIP, callback_data="skip")])
    
    return InlineKeyboardMarkup(buttons)


def get_what_to_print_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа печати."""
    buttons = [
        [InlineKeyboardButton("Визитки", callback_data="business_cards")],
        [InlineKeyboardButton("Флаеры", callback_data="booklets")],
        [InlineKeyboardButton("Баннеры", callback_data="banners")],
        [InlineKeyboardButton("Плакаты", callback_data="posters")],
        [InlineKeyboardButton("Наклейки", callback_data="stickers")],
        [InlineKeyboardButton("Другое", callback_data="other")],
        [InlineKeyboardButton(BTN_BACK, callback_data="back")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_format_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора формата."""
    buttons = [
        [InlineKeyboardButton("A4 (210×297 мм)", callback_data="a4")],
        [InlineKeyboardButton("A5 (148×210 мм)", callback_data="a5")],
        [InlineKeyboardButton("A6 (105×148 мм)", callback_data="a6")],
        [InlineKeyboardButton("A3 (297×420 мм)", callback_data="a3")],
        [InlineKeyboardButton("Баннер произвольного размера", callback_data="banner")],
        [InlineKeyboardButton("Другой размер", callback_data="other")],
        [InlineKeyboardButton(BTN_BACK, callback_data="back")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_sides_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора сторон печати."""
    buttons = [
        [InlineKeyboardButton("Односторонняя", callback_data="1_sided")],
        [InlineKeyboardButton("Двусторонняя", callback_data="2_sided")],
        [InlineKeyboardButton(BTN_BACK, callback_data="back")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_color_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора цветности."""
    buttons = [
        [InlineKeyboardButton("4+0 (цветная с одной стороны)", callback_data="4_0")],
        [InlineKeyboardButton("4+4 (цветная с двух сторон)", callback_data="4_4")],
        [InlineKeyboardButton("Ч/Б (черно-белая)", callback_data="1_0")],
        [InlineKeyboardButton(BTN_BACK, callback_data="back")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_paper_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора бумаги."""
    buttons = [
        [InlineKeyboardButton("130 г/м²", callback_data="130")],
        [InlineKeyboardButton("170 г/м²", callback_data="170")],
        [InlineKeyboardButton("300 г/м²", callback_data="300")],
        [InlineKeyboardButton("Другая", callback_data="other")],
        [InlineKeyboardButton(BTN_BACK, callback_data="back")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_finishing_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора постпечатной обработки."""
    buttons = [
        [InlineKeyboardButton("Ламинация", callback_data="lamination")],
        [InlineKeyboardButton("Биговка", callback_data="scoring")],
        [InlineKeyboardButton("Фальцовка", callback_data="folding")],
        [InlineKeyboardButton("Вырубка", callback_data="cutting")],
        [InlineKeyboardButton("Без обработки", callback_data="none")],
        [InlineKeyboardButton(BTN_BACK, callback_data="back")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_has_layout_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора наличия макета."""
    buttons = [
        [InlineKeyboardButton("Да, есть макет", callback_data="yes")],
        [InlineKeyboardButton("Нет макета", callback_data="no")],
        [InlineKeyboardButton("Нужен дизайнер", callback_data="designer")],
        [InlineKeyboardButton(BTN_BACK, callback_data="back")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа."""
    buttons = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm")],
        [InlineKeyboardButton("✏️ Изменить", callback_data="edit")],
        [InlineKeyboardButton("👨‍💼 Позвать оператора", callback_data="call_operator")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_operator_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для операторов (новый формат callback_data)."""
    buttons = [
        [
            InlineKeyboardButton("🛠 Принять", callback_data=make_cb(OP_TAKE, order_id)),
            InlineKeyboardButton("✅ Готово", callback_data=make_cb(OP_READY, order_id))
        ],
        [
            InlineKeyboardButton("✏️ Нужны правки", callback_data=make_cb(OP_NEEDS_FIX, order_id)),
            InlineKeyboardButton("📨 Связаться с клиентом", callback_data=make_cb(OP_CONTACT, order_id))
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_cancel_confirm_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton("✅ Да, отменить", callback_data=CANCEL_YES)],
        [InlineKeyboardButton("↩️ Нет, продолжить", callback_data=CANCEL_NO)],
    ]
    return InlineKeyboardMarkup(kb)


def get_bc_qty_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора тиража визиток."""
    return ReplyKeyboardMarkup(
        [["50", "100"], ["500", "1000"], [BTN_BACK, BTN_CANCEL]], 
        resize_keyboard=True, 
        is_persistent=True
    )


def get_bc_size_keyboard(allow_custom: bool = False) -> ReplyKeyboardMarkup:
    """Клавиатура для выбора размера визиток."""
    buttons = [[BTN_BC_SIZE]]
    if allow_custom:
        buttons.append(["Ваш размер"])
    buttons.append([BTN_BACK, BTN_CANCEL])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, is_persistent=True)


def get_sides_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора сторон печати."""
    return ReplyKeyboardMarkup(
        [[BTN_1, BTN_2], [BTN_BACK, BTN_CANCEL]], 
        resize_keyboard=True, 
        is_persistent=True
    )


def get_fly_format_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для выбора формата буклета."""
    return ReplyKeyboardMarkup(
        [["A7 105×74", "A6 105×148"], ["A5 210×148", "A4 210×297"], [BTN_BACK, BTN_CANCEL]], 
        resize_keyboard=True, 
        is_persistent=True
    )


def get_upload_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для загрузки макета."""
    return ReplyKeyboardMarkup(
        [[BTN_NEXT], [BTN_BACK, BTN_CANCEL]], 
        resize_keyboard=True, 
        is_persistent=True
    )


def get_notes_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для пожеланий."""
    return ReplyKeyboardMarkup(
        [[BTN_SKIP], [BTN_BACK, BTN_CANCEL]], 
        resize_keyboard=True, 
        is_persistent=True
    )


def get_confirm_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для подтверждения."""
    return ReplyKeyboardMarkup(
        [[BTN_SUBMIT], [BTN_BACK, BTN_CANCEL]], 
        resize_keyboard=True, 
        is_persistent=True
    )


def get_layout_keyboard() -> ReplyKeyboardMarkup:
    kb = [[BTN_NEXT, BTN_CANCEL], [BTN_BACK]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True, is_persistent=True, one_time_keyboard=False)


def orders_list_inline(items, has_more=False):
    """Инлайн-клавиатура для списка заказов."""
    rows = [[InlineKeyboardButton(f"{title} {status}", callback_data=f"ord:{oid}")]
            for oid, title, status in items]
    if has_more:
        rows.append([InlineKeyboardButton(BTN_LOAD_MORE, callback_data="ord:more")])
    return InlineKeyboardMarkup(rows)


def get_sheet_format_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора формата листа."""
    return ReplyKeyboardMarkup(
        [
            ["A5 (210×148 мм)", "A4 (297×210 мм)"],
            ["A3 (420×297 мм)", "Ваш размер"],
            [BTN_BACK, BTN_CANCEL]
        ],
        resize_keyboard=True,
        is_persistent=True
    )


def get_postpress_keyboard(lamination: str = "none", bigovka_count: int = 0, corner_rounding: bool = False) -> ReplyKeyboardMarkup:
    """Клавиатура постпечатной обработки с текущими значениями."""
    lamination_labels = {
        "none": "Ламинация (нет)",
        "matte": "Ламинация (мат)",
        "glossy": "Ламинация (глянец)"
    }
    
    bigovka_text = f"Биговка ({bigovka_count})" if bigovka_count > 0 else "Биговка"
    corner_text = "Скругление углов (да)" if corner_rounding else "Скругление углов (нет)"
    
    return ReplyKeyboardMarkup(
        [
            [lamination_labels.get(lamination, "Ламинация (нет)")],
            [bigovka_text],
            [corner_text],
            ["Без обработки"],
            [BTN_NEXT],
            [BTN_BACK, BTN_CANCEL]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

# alias for backward compatibility (импорт из старого кода)
get_postprocess_keyboard = get_postpress_keyboard


def get_cancel_choice_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора отмены."""
    return ReplyKeyboardMarkup(
        [
            ["↩️ Только этот шаг"],
            ["🗑 Полностью отменить заказ"],
            [BTN_BACK]
        ],
        resize_keyboard=True,
        is_persistent=True
    )


def get_format_selection_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора формата."""
    return ReplyKeyboardMarkup([
        ["A7 (105×74 мм)", "A6 (148×105 мм)"],
        ["A5 (210×148 мм)", "A4 (297×210 мм)"],
        ["A3 (420×297 мм)", "A2 (594×420 мм)"],
        ["A1 (841×594 мм)", "Ваш размер"],
        [BTN_BACK, BTN_CANCEL]
    ], resize_keyboard=True, is_persistent=True)


def get_material_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора материала для наклеек."""
    return ReplyKeyboardMarkup([
        ["📄 Бумага", "🎯 Винил"],
        [BTN_BACK, BTN_CANCEL]
    ], resize_keyboard=True, is_persistent=True)


def get_print_color_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора цветности печати."""
    return ReplyKeyboardMarkup([
        ["🎨 Цветная", "⚫ Ч/Б"],
        [BTN_BACK, BTN_CANCEL]
    ], resize_keyboard=True, is_persistent=True)


def get_banner_size_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для ввода размера баннера."""
    return ReplyKeyboardMarkup([
        [BTN_BACK, BTN_CANCEL]
    ], resize_keyboard=True, is_persistent=True)


def get_print_format_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора формата для обычной печати."""
    return ReplyKeyboardMarkup([
        ["A4 (210×297 мм)", "A3 (297×420 мм)"],
        [BTN_BACK, BTN_CANCEL]
    ], resize_keyboard=True, is_persistent=True)


def get_print_type_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора типа печати."""
    return ReplyKeyboardMarkup([
        ["🖤 Чёрно-белая", "🎨 Цветная"],
        [BTN_BACK, BTN_CANCEL]
    ], resize_keyboard=True, is_persistent=True)


def get_postpress_options_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора дополнительных параметров постобработки."""
    return ReplyKeyboardMarkup([
        ["✨ Ламинация (мат)", "✨ Ламинация (глянец)"],
        ["➖ Биговка", "🔘 Скругление углов"],
        ["Нет", BTN_BACK]
    ], resize_keyboard=True, is_persistent=True)


def get_smart_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура умной отмены."""
    return ReplyKeyboardMarkup([
        ["↩️ Только шаг", "🗑 Весь заказ"]
    ], resize_keyboard=True, is_persistent=True)