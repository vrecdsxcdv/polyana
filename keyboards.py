from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

BTN_BACK   = "⬅️ Назад"
BTN_CANCEL = "❌ Отмена"
BTN_NEXT   = "➡️ Далее"
BTN_SKIP   = "⏭️ Пропустить"
BTN_SUBMIT = "Готово"
BTN_BC_SIZE = "Визитка 90×50"
BTN_1 = "Односторонняя"
BTN_2 = "Двусторонняя"

def get_keyboard_remove(): return ReplyKeyboardRemove()

def get_home_keyboard():
    return ReplyKeyboardMarkup(
        [["📝 Новый заказ"], ["📦 Мои заказы","☎️ Связаться с оператором"], ["❓ Помощь"]],
        resize_keyboard=True, is_persistent=True)

def get_product_keyboard():
    return ReplyKeyboardMarkup([
        ["🪪 Визитки","📄 Флаеры"],
        ["🖼 Баннеры","📰 Плакаты"],
        ["🏷 Наклейки","📚 Листы"],
        ["📦 Другое"],
        [BTN_BACK, BTN_CANCEL]
    ], resize_keyboard=True, is_persistent=True)

def get_bc_qty_keyboard():
    return ReplyKeyboardMarkup([["50","100"],["500","1000"],[BTN_BACK, BTN_CANCEL]],
                               resize_keyboard=True, is_persistent=True)

def get_bc_size_keyboard():
    return ReplyKeyboardMarkup([[BTN_BC_SIZE],[BTN_BACK, BTN_CANCEL]],
                               resize_keyboard=True, is_persistent=True)

def get_sides_keyboard():
    return ReplyKeyboardMarkup([[BTN_1, BTN_2],[BTN_BACK, BTN_CANCEL]],
                               resize_keyboard=True, is_persistent=True)

def get_format_selection_keyboard():
    return ReplyKeyboardMarkup([
        ["A7 (105×74 мм)","A6 (148×105 мм)"],
        ["A5 (210×148 мм)","A4 (297×210 мм)"],
        ["A3 (420×297 мм)","A2 (594×420 мм)"],
        ["A1 (841×594 мм)","Ваш размер"],
        [BTN_BACK, BTN_CANCEL]
    ], resize_keyboard=True, is_persistent=True)

def get_material_keyboard():
    return ReplyKeyboardMarkup([["📄 Бумага","🎯 Винил"],[BTN_BACK, BTN_CANCEL]],
                               resize_keyboard=True, is_persistent=True)

def get_print_color_keyboard():
    return ReplyKeyboardMarkup([["🎨 Цветная","⚫ Ч/Б"],[BTN_BACK, BTN_CANCEL]],
                               resize_keyboard=True, is_persistent=True)

def get_postpress_keyboard(lamination="none", bigo=0, cr=False):
    lam = {"none":"✨ Ламинация (нет)","matte":"✨ Ламинация (мат)","glossy":"✨ Ламинация (глянец)"}[lamination]
    return ReplyKeyboardMarkup([
        [lam],
        [f"➖ Биговка ({bigo} линий)" if bigo else "➖ Биговка", f"🔘 Скругление углов ({'да' if cr else 'нет'})"],
        ["➡️ Далее","⬅️ Назад"],
        ["❌ Отмена"]
    ], resize_keyboard=True, is_persistent=True)

def get_upload_keyboard():
    return ReplyKeyboardMarkup([[BTN_NEXT],[BTN_BACK, BTN_CANCEL]],
                               resize_keyboard=True, is_persistent=True)

def get_notes_keyboard():
    return ReplyKeyboardMarkup([[BTN_SKIP],[BTN_BACK, BTN_CANCEL]],
                               resize_keyboard=True, is_persistent=True)

def get_confirm_keyboard():
    return ReplyKeyboardMarkup([[BTN_SUBMIT],[BTN_BACK, BTN_CANCEL]],
                               resize_keyboard=True, is_persistent=True)

def get_cancel_choice_keyboard():
    return ReplyKeyboardMarkup([["↩️ Только этот шаг"],["🗑 Полностью отменить заказ"],[BTN_BACK]],
                               resize_keyboard=True, is_persistent=True)