from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from config import config

PAGE_SIZE = 10

def _is_operator_chat(update: Update) -> bool:
    chat = update.effective_chat
    return chat and chat.id == config.OPERATOR_CHAT_ID

def _is_admin(update: Update) -> bool:
    uid = update.effective_user.id if update.effective_user else 0
    return uid in config.ADMIN_IDS

def _format_row(o):
    # ожидаем поля: code, category, quantity, status, user_name/phone
    cat = getattr(o, "what_to_print", "—")
    qty = getattr(o, "quantity", 1)
    st  = getattr(o, "status", "new")
    code= getattr(o, "code", "—")
    return f"№{code} • {cat} • x{qty} • {st}"

def _kb_row(order_id):
    return [InlineKeyboardButton("Открыть", callback_data=f"adm_open:{order_id}")]

async def _fetch_orders(offset: int, limit: int):
    # Используем существующий сервис
    from services.orders import list_active_orders
    res = list_active_orders(offset=offset, limit=limit)
    orders = res[0] if isinstance(res, tuple) else res
    # Отфильтруем «готовые» статусы
    exclude_statuses = ["DONE", "COMPLETED", "Готово", "ready", "done", "completed"]
    orders = [o for o in orders if str(getattr(o, "status", "")).upper() not in exclude_statuses]
    return orders

async def _fetch_order(order_id: int):
    from services.orders import get_order_by_code
    # Простая заглушка - в реальности нужен поиск по ID
    return None

async def all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_operator_chat(update): 
        await update.effective_message.reply_text("Команда доступна только в операторском чате.")
        return
    if not _is_admin(update):
        await update.effective_message.reply_text("Только для операторов.")
        return
    context.user_data["adm_offset"] = 0
    await _render_page(update, context, 0)

async def _render_page(update: Update, context: ContextTypes.DEFAULT_TYPE, offset: int):
    data = await _fetch_orders(offset, PAGE_SIZE)
    if not data:
        await update.effective_message.reply_text("Заказов в работе нет.")
        return
    lines = [ _format_row(o) for o in data ]
    rows  = [ _kb_row(getattr(o, "id", 0)) for o in data ]
    # пагинация
    nav=[]
    if offset>0: nav.append(InlineKeyboardButton("« Назад", callback_data=f"adm_page:{offset-PAGE_SIZE}"))
    if len(data)==PAGE_SIZE: nav.append(InlineKeyboardButton("Вперёд »", callback_data=f"adm_page:{offset+PAGE_SIZE}"))
    if nav: rows.append(nav)
    await update.effective_message.reply_text(
        "📋 Заказы (в работе):\n" + "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(rows)
    )

async def on_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_operator_chat(update) or not _is_admin(update):
        await update.callback_query.answer("Нет доступа", show_alert=True)
        return
    await update.callback_query.answer()
    data = update.callback_query.data
    if data.startswith("adm_page:"):
        offset = int(data.split(":")[1])
        await _render_page(update, context, offset)
        return
    if data.startswith("adm_open:"):
        oid = int(data.split(":")[1])
        order = await _fetch_order(oid)
        if not order:
            await update.effective_message.reply_text("Заказ не найден.")
            return
        # компактная карточка
        txt = (
            f"№{order['code']}\n"
            f"Категория: {order.get('category_title','—')}\n"
            f"Кол-во: {order.get('quantity',1)}\n"
            f"Статус: {order.get('status','—')}\n"
            f"Клиент: {order.get('client','—')}\n"
        )
        await update.effective_message.reply_text(txt)
        return