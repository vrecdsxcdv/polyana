import logging, re, asyncio
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, filters
from states import OrderStates
from keyboards import *
from texts import *
from services.normalize import is_btn, norm_btn
from services.validators import *
from services.formatting import format_order_summary
from services.notifier import send_order_to_operators
from config import config

logger=logging.getLogger(__name__)

BACK_RE = r"^⬅️?\s*Назад$"
NEXT_RE = r"^➡️?\s*Далее$"
SKIP_RE = r"^⏭️?\s*Пропустить$"
SUBMIT_RE = r"^Готово$"

STACK_KEY="__state_stack__"
CUR_KEY="__cur__"
def _stack(ctx): return ctx.user_data.setdefault(STACK_KEY, [])
def push_state(ctx, st): 
    stck=_stack(ctx)
    if not stck or stck[-1]!=st: stck.append(st)
def pop_state(ctx):
    stck=_stack(ctx)
    if stck: stck.pop()
    return stck[-1] if stck else ConversationHandler.END
def set_cur(ctx, st): ctx.user_data[CUR_KEY]=st
def get_cur(ctx): return ctx.user_data.get(CUR_KEY)

async def render_state(update, context, st):
    set_cur(context, st)
    reply=(update.message or update.effective_message).reply_text
    if st==OrderStates.PRODUCT:
        await reply("Обновляю меню…", reply_markup=get_keyboard_remove())
        await reply(ASK_PRODUCT, reply_markup=get_product_keyboard()); return st
    if st==OrderStates.BC_QTY:
        await reply(ASK_BC_QTY, reply_markup=get_bc_qty_keyboard()); return st
    if st==OrderStates.BC_SIZE:
        await reply(ASK_BC_SIZE, reply_markup=get_bc_size_keyboard()); return st
    if st==OrderStates.BC_SIDES:
        await reply(ASK_BC_SIDES, reply_markup=get_sides_keyboard()); return st
    if st==OrderStates.FLY_FORMAT:
        await reply(ASK_FLY_FORMAT, reply_markup=get_format_selection_keyboard()); return st
    if st==OrderStates.FLY_SIDES:
        await reply(ASK_FLY_SIDES, reply_markup=get_sides_keyboard()); return st
    if st==OrderStates.ORDER_SHEET_FORMAT:
        await reply(ASK_SHEET_FORMAT, reply_markup=get_format_selection_keyboard()); return st
    if st==OrderStates.ORDER_CUSTOM_SIZE:
        await reply(ASK_CUSTOM_SIZE, reply_markup=get_keyboard_remove()); return st
    if st==OrderStates.ORDER_POSTPRESS:
        lam=context.user_data.get("lamination","none")
        bigo=context.user_data.get("bigovka_count",0)
        cr=bool(context.user_data.get("corner_rounding",False))
        await reply(ASK_POSTPRESS, reply_markup=get_postpress_keyboard(lam,bigo,cr)); return st
    if st==OrderStates.ORDER_POSTPRESS_BIGOVKA:
        await reply(ASK_BIGOVKA_COUNT, reply_markup=get_keyboard_remove()); return st
    if st==OrderStates.ORDER_BANNER_SIZE:
        await reply(ASK_BANNER_SIZE, reply_markup=get_keyboard_remove()); return st
    if st==OrderStates.ORDER_MATERIAL:
        await reply(ASK_MATERIAL, reply_markup=get_material_keyboard()); return st
    if st==OrderStates.ORDER_PRINT_COLOR:
        await reply(ASK_PRINT_COLOR, reply_markup=get_print_color_keyboard()); return st
    if st==OrderStates.ORDER_UPLOAD:
        await reply(UPLOAD_PROMPT.format(max_mb=config.MAX_UPLOAD_MB), reply_markup=get_upload_keyboard()); return st
    if st==OrderStates.ORDER_DUE:
        await reply(ASK_DUE, reply_markup=get_notes_keyboard()); return st
    if st==OrderStates.ORDER_PHONE:
        await reply(ASK_PHONE, reply_markup=get_notes_keyboard()); return st
    if st==OrderStates.ORDER_NOTES:
        await reply(ASK_NOTES, reply_markup=get_notes_keyboard()); return st
    if st==OrderStates.ORDER_CONFIRM:
        await reply("✅ Подтверждение заказа\n\n"+format_order_summary(context.user_data),
                    reply_markup=get_confirm_keyboard()); return st
    await reply("Чем ещё помочь?", reply_markup=get_home_keyboard()); return ConversationHandler.END

async def start_order(update:Update, context:ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    push_state(context, OrderStates.PRODUCT)
    return await render_state(update, context, OrderStates.PRODUCT)

async def handle_back(update:Update, context:ContextTypes.DEFAULT_TYPE):
    prev = pop_state(context)
    if prev==ConversationHandler.END:
        return await render_state(update, context, OrderStates.PRODUCT)
    return await render_state(update, context, prev)

async def handle_product(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if is_btn(text,"отмена"): return await handle_cancel(update, context)
    if is_btn(text,"назад"):  return await handle_back(update, context)

    if is_btn(text,"визитки"):
        context.user_data.update(what_to_print="Визитки", product_type="bc")
        push_state(context, OrderStates.BC_QTY)
        return await render_state(update, context, OrderStates.BC_QTY)

    if is_btn(text,"флаеры"):
        context.user_data.update(what_to_print="Флаеры", product_type="fly")
        push_state(context, OrderStates.BC_QTY)        # сначала спросим тираж
        return await render_state(update, context, OrderStates.BC_QTY)

    if is_btn(text,"баннеры"):
        context.user_data.update(what_to_print="Баннеры", product_type="banner")
        from texts import CONTACTS_MESSAGE, BANNERS_REDIRECT
        await update.message.reply_text(BANNERS_REDIRECT.format(contacts=CONTACTS_MESSAGE), reply_markup=get_home_keyboard())
        try:
            await send_order_to_operators(context.bot, "Клиент выбрал баннеры. Нужна помощь оператора.", int(config.OPERATOR_CHAT_ID))
        except Exception:
            pass
        context.user_data.clear()
        return ConversationHandler.END

    if is_btn(text,"плакаты"):
        context.user_data.update(what_to_print="Плакаты", product_type="poster")
        push_state(context, OrderStates.BC_QTY)
        return await render_state(update, context, OrderStates.BC_QTY)

    if is_btn(text,"наклейки"):
        context.user_data.update(what_to_print="Наклейки", product_type="sticker")
        push_state(context, OrderStates.BC_QTY)
        return await render_state(update, context, OrderStates.BC_QTY)

    if is_btn(text,"листы"):
        context.user_data.update(what_to_print="Листы", product_type="sheets")
        push_state(context, OrderStates.BC_QTY)
        return await render_state(update, context, OrderStates.BC_QTY)

    if is_btn(text,"другое"):
        context.user_data.update(what_to_print="Другое", product_type="other")
        push_state(context, OrderStates.ORDER_SHEET_FORMAT)
        return await render_state(update, context, OrderStates.ORDER_SHEET_FORMAT)

    await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_product_keyboard())
    return OrderStates.PRODUCT

async def handle_bc_qty(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if re.match(BACK_RE, text): return await handle_back(update, context)
    n=to_int(text)
    if n is None: await update.message.reply_text(ERR_INT, reply_markup=get_bc_qty_keyboard()); return OrderStates.BC_QTY
    if context.user_data.get("product_type")=="bc":
        if not is_multiple_of_50(n):
            await update.message.reply_text(ERR_BC_STEP, reply_markup=get_bc_qty_keyboard()); return OrderStates.BC_QTY
    context.user_data["quantity"]=n

    p=context.user_data.get("product_type")
    if p in ("fly","poster","sticker","sheets","other"):
        push_state(context, OrderStates.ORDER_SHEET_FORMAT)
        return await render_state(update, context, OrderStates.ORDER_SHEET_FORMAT)
    if p=="bc":
        push_state(context, OrderStates.BC_SIZE)
        return await render_state(update, context, OrderStates.BC_SIZE)
    return await render_state(update, context, OrderStates.PRODUCT)

async def handle_bc_size(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if re.match(BACK_RE, text): return await handle_back(update, context)
    if text==BTN_BC_SIZE:
        context.user_data["format"]="90×50"
        context.user_data["paper"]="300 г/м²"
        push_state(context, OrderStates.BC_SIDES)
        return await render_state(update, context, OrderStates.BC_SIDES)
    await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_bc_size_keyboard())
    return OrderStates.BC_SIZE

async def handle_bc_sides(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if re.match(BACK_RE, text): return await handle_back(update, context)
    if text==BTN_1: context.user_data["sides"]="1"
    elif text==BTN_2: context.user_data["sides"]="2"
    else:
        await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_sides_keyboard()); return OrderStates.BC_SIDES
    push_state(context, OrderStates.ORDER_POSTPRESS)
    return await render_state(update, context, OrderStates.ORDER_POSTPRESS)

async def handle_sheet_format(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if re.match(BACK_RE, text): return await handle_back(update, context)
    mapping={
      "A7 (105×74 мм)":("A7","105×74"),"A6 (148×105 мм)":("A6","148×105"),
      "A5 (210×148 мм)":("A5","210×148"),"A4 (297×210 мм)":("A4","297×210"),
      "A3 (420×297 мм)":("A3","420×297"),"A2 (594×420 мм)":("A2","594×420"),
      "A1 (841×594 мм)":("A1","841×594"),
    }
    if text=="Ваш размер":
        push_state(context, OrderStates.ORDER_CUSTOM_SIZE)
        return await render_state(update, context, OrderStates.ORDER_CUSTOM_SIZE)
    if text in mapping:
        sf, fmt = mapping[text]
        context.user_data["sheet_format"]=sf; context.user_data["format"]=fmt
    else:
        await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_format_selection_keyboard()); return OrderStates.ORDER_SHEET_FORMAT

    p=context.user_data.get("product_type")
    if p=="banner":
        push_state(context, OrderStates.ORDER_POSTPRESS); return await render_state(update, context, OrderStates.ORDER_POSTPRESS)
    if p=="sticker":
        push_state(context, OrderStates.ORDER_MATERIAL); return await render_state(update, context, OrderStates.ORDER_MATERIAL)
    if p in ("fly","poster","sheets","other"):
        push_state(context, OrderStates.BC_SIDES); return await render_state(update, context, OrderStates.BC_SIDES)
    push_state(context, OrderStates.BC_SIDES); return await render_state(update, context, OrderStates.BC_SIDES)

async def handle_custom_size(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if re.match(BACK_RE, text): return await handle_back(update, context)
    size=parse_custom_size(text)
    if not size: await update.message.reply_text(ERR_SIZE_FORMAT); return OrderStates.ORDER_CUSTOM_SIZE
    w,h=size; context.user_data["sheet_format"]="custom"; context.user_data["custom_size_mm"]=f"{w}×{h} мм"; context.user_data["format"]=f"{w}×{h}"
    p=context.user_data.get("product_type")
    if p=="sticker":
        push_state(context, OrderStates.ORDER_MATERIAL); return await render_state(update, context, OrderStates.ORDER_MATERIAL)
    push_state(context, OrderStates.BC_SIDES); return await render_state(update, context, OrderStates.BC_SIDES)

async def handle_postpress(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if is_btn(text,"назад"): return await handle_back(update, context)
    if is_btn(text,"отмена"): return await handle_cancel(update, context)
    if is_btn(text,"далее"):
        push_state(context, OrderStates.ORDER_UPLOAD); return await render_state(update, context, OrderStates.ORDER_UPLOAD)
    if text.startswith("✨ Ламинация"):
        if "(мат)" in text: context.user_data["lamination"]="matte"
        elif "(глянец)" in text: context.user_data["lamination"]="glossy"
        else: context.user_data["lamination"]="none"
    elif text.startswith("➖ Биговка"):
        push_state(context, OrderStates.ORDER_POSTPRESS_BIGOVKA); return await render_state(update, context, OrderStates.ORDER_POSTPRESS_BIGOVKA)
    elif text.startswith("🔘 Скругление"):
        context.user_data["corner_rounding"]=not context.user_data.get("corner_rounding",False)
    lam=context.user_data.get("lamination","none"); bigo=context.user_data.get("bigovka_count",0); cr=context.user_data.get("corner_rounding",False)
    await update.message.reply_text(ASK_POSTPRESS, reply_markup=get_postpress_keyboard(lam,bigo,cr))
    return OrderStates.ORDER_POSTPRESS

async def handle_postpress_bigovka(update:Update, context:ContextTypes.DEFAULT_TYPE):
    n=parse_bigovka_count(update.message.text)
    if n is None: await update.message.reply_text(ERR_BIGOVKA_INT); return OrderStates.ORDER_POSTPRESS_BIGOVKA
    context.user_data["bigovka_count"]=n
    lam=context.user_data.get("lamination","none"); cr=context.user_data.get("corner_rounding",False)
    await update.message.reply_text(f"✅ Биговка ({n} линий) сохранена.\n\n{ASK_POSTPRESS}",
                                    reply_markup=get_postpress_keyboard(lam,n,cr))
    return OrderStates.ORDER_POSTPRESS

async def handle_banner_size(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if re.match(BACK_RE, text): return await handle_back(update, context)
    size=parse_banner_size(text)
    if not size: await update.message.reply_text("❌ Формат: например 2×1.5"); return OrderStates.ORDER_BANNER_SIZE
    w,h=size; context.user_data.update(sheet_format="custom", custom_size_mm=f"{w}×{h} м", format=f"{w}×{h} м")
    push_state(context, OrderStates.ORDER_POSTPRESS); return await render_state(update, context, OrderStates.ORDER_POSTPRESS)

async def handle_material(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if re.match(BACK_RE, text): return await handle_back(update, context)
    if "Бумага" in text: context.user_data["material"]="paper"
    elif "Винил" in text: context.user_data["material"]="vinyl"
    else:
        await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_material_keyboard()); return OrderStates.ORDER_MATERIAL
    push_state(context, OrderStates.ORDER_PRINT_COLOR); return await render_state(update, context, OrderStates.ORDER_PRINT_COLOR)

async def handle_print_color(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if re.match(BACK_RE, text): return await handle_back(update, context)
    if "Цветн" in text: context.user_data["print_color"]="color"
    elif "Ч/Б" in text or "ЧБ" in text or "Чёр" in text or "Черн" in text: context.user_data["print_color"]="bw"
    else:
        await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_print_color_keyboard()); return OrderStates.ORDER_PRINT_COLOR
    push_state(context, OrderStates.BC_SIDES); return await render_state(update, context, OrderStates.BC_SIDES)

async def handle_upload(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        doc=update.message.document
        if not (doc.mime_type or "").startswith("application/pdf"):
            await update.message.reply_text(ERR_ONLY_PDF, reply_markup=get_upload_keyboard()); return OrderStates.ORDER_UPLOAD
        context.user_data.setdefault("attachments", []).append({"file_id":doc.file_id,"mime_type":doc.mime_type,"name":doc.file_name})
        await update.message.reply_text(UPLOAD_OK, reply_markup=get_upload_keyboard()); return OrderStates.ORDER_UPLOAD
    if re.match(BACK_RE, update.message.text): return await handle_back(update, context)
    if re.match(NEXT_RE, update.message.text):
        if not any((a.get("mime_type") or "").startswith("application/pdf") for a in context.user_data.get("attachments",[])):
            await update.message.reply_text(ERR_ONLY_PDF, reply_markup=get_upload_keyboard()); return OrderStates.ORDER_UPLOAD
        push_state(context, OrderStates.ORDER_DUE); return await render_state(update, context, OrderStates.ORDER_DUE)
    await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_upload_keyboard()); return OrderStates.ORDER_UPLOAD

async def handle_due(update:Update, context:ContextTypes.DEFAULT_TYPE):
    try:
        dt=parse_due(update.message.text, config.TIMEZONE); 
        if not dt: raise ValueError
        context.user_data["deadline_at"]=dt
        push_state(context, OrderStates.ORDER_PHONE); return await render_state(update, context, OrderStates.ORDER_PHONE)
    except:
        await update.message.reply_text(ERR_DATE, reply_markup=get_notes_keyboard()); return OrderStates.ORDER_DUE

async def handle_phone(update:Update, context:ContextTypes.DEFAULT_TYPE):
    p=normalize_phone(update.message.text)
    if not p: await update.message.reply_text(ERR_PHONE, reply_markup=get_notes_keyboard()); return OrderStates.ORDER_PHONE
    context.user_data["contact"]=p
    push_state(context, OrderStates.ORDER_NOTES); return await render_state(update, context, OrderStates.ORDER_NOTES)

async def handle_notes(update:Update, context:ContextTypes.DEFAULT_TYPE):
    t=update.message.text
    if re.match(SKIP_RE, t): context.user_data["notes"]=""
    else: context.user_data["notes"]=t[:1000]
    push_state(context, OrderStates.ORDER_CONFIRM); return await render_state(update, context, OrderStates.ORDER_CONFIRM)

async def handle_confirm(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if re.match(SUBMIT_RE, update.message.text):
        summary = format_order_summary(context.user_data)
        await update.message.reply_text("✅ Заказ создан!\n\n"+summary, reply_markup=get_home_keyboard())
        # зеркалим оператору
        try:
            await send_order_to_operators(context.bot, summary, int(config.OPERATOR_CHAT_ID))
            for a in context.user_data.get("attachments",[]):
                await context.bot.send_document(int(config.OPERATOR_CHAT_ID), a["file_id"], caption="Макет PDF")
        except Exception as e:
            logger.warning("operator notify fail: %s", e)
        context.user_data.clear()
        return ConversationHandler.END
    await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_confirm_keyboard()); return OrderStates.ORDER_CONFIRM

async def handle_cancel(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ASK_CANCEL_CHOICE, reply_markup=get_cancel_choice_keyboard())
    return OrderStates.CANCEL_CHOICE

async def handle_cancel_choice(update:Update, context:ContextTypes.DEFAULT_TYPE):
    t=update.message.text
    if t.startswith("↩️"):
        return await handle_back(update, context)
    if t.startswith("🗑"):
        context.user_data.clear(); await update.message.reply_text("❌ Заказ отменён.", reply_markup=get_home_keyboard())
        return ConversationHandler.END
    await update.message.reply_text(REMIND_USE_BTNS, reply_markup=get_cancel_choice_keyboard()); return OrderStates.CANCEL_CHOICE