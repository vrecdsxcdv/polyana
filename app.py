import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# NEW: env helpers
from loguru import logger

def env_int(name: str, default: int | None = None) -> int | None:
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        logger.error(f"ENV {name} must be integer, got: {val!r}")
        return default

# NEW: Changed from BOT_TOKEN to TELEGRAM_BOT_TOKEN
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is empty. Set it in Railway → Variables")

import logging, logging.handlers
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, filters, Defaults
from datetime import timezone
from config import config
from database import create_tables, safe_migrate
from states import OrderStates
from handlers.common import start_command, help_command, my_orders_command, status_command, call_operator_command, error_handler, main_menu_router
from handlers.order_flow import eff_msg
from handlers.order_flow import (
    start_order, handle_category, handle_quantity, handle_bc_qty, handle_office_format, handle_office_color,
    handle_poster_format, handle_poster_lamination, handle_bc_format, handle_bc_sides, handle_bc_lamination,
    handle_fly_format, handle_fly_sides, handle_sticker_size, handle_sticker_material,
    handle_sticker_color, handle_files, handle_due, handle_phone, handle_notes, handle_confirm,
    handle_back, handle_cancel, handle_cancel_choice, CANCEL_RE, BACK_RE, SKIP_RE,
    reset_to_start, unknown_command_during_flow, handle_back_from_categories
)
from handlers.status import handle_status_callback
from handlers.admin import all_orders, on_admin_callback
from handlers.orders_view import cb_view_order
from handlers.common_contacts import handle_contact_operator
from keyboards import BTN_NEW_ORDER, BTN_MY_ORDERS, BTN_CALL_OPERATOR, BTN_HELP, NAV_BACK, NAV_CANCEL, BTN_BACK

def setup_logging():
    fh=logging.handlers.RotatingFileHandler("bot.log",maxBytes=1_000_000,backupCount=3)
    fmt=logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(fmt); root=logging.getLogger(); root.setLevel(logging.INFO); root.addHandler(fh); root.addHandler(logging.StreamHandler())

def create_application():
    defaults=Defaults(parse_mode="HTML")
    app=ApplicationBuilder().token(config.BOT_TOKEN).defaults(defaults).get_updates_connection_pool_size(4)\
        .read_timeout(10).connect_timeout(10).pool_timeout(5).build()
    create_tables(); safe_migrate()

    conv = ConversationHandler(
        entry_points=[CommandHandler("neworder", start_order), MessageHandler(filters.Regex("^🧾 Новый заказ$"), start_order)],
        states={
            OrderStates.CHOOSE_CATEGORY: [
                # 1) Назад -> /start (должен идти первым!)
                MessageHandler(filters.Regex(rf"^(?:⬅️|↩️)\\s*Назад$"), start_command),

                # 2) Остальные тексты — это выбор категории
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category)
            ],
            OrderStates.QUANTITY: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity)
            ],
            OrderStates.BC_QTY: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bc_qty)
            ],
            
            # Офисная бумага
            OrderStates.OFFICE_FORMAT: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_office_format)
            ],
            OrderStates.OFFICE_COLOR: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_office_color)
            ],
            
            # Плакаты
            OrderStates.POSTER_FORMAT: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_poster_format)
            ],
            OrderStates.ORDER_POSTPRESS: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_poster_lamination)
            ],
            
            # Визитки
            OrderStates.BC_FORMAT: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bc_format)
            ],
            OrderStates.BC_SIDES: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bc_sides)
            ],
            OrderStates.BC_LAMINATION: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bc_lamination)
            ],
            
            # Флаеры
            OrderStates.FLY_FORMAT: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fly_format)
            ],
            OrderStates.FLY_SIDES: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fly_sides)
            ],
            
            # Наклейки
            OrderStates.STICKER_SIZE: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sticker_size)
            ],
            OrderStates.STICKER_MATERIAL: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sticker_material)
            ],
            OrderStates.STICKER_COLOR: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sticker_color)
            ],
            
            # Общие шаги
            OrderStates.ORDER_FILES: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.Document.ALL, handle_files),
                MessageHandler(filters.PHOTO, handle_files),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_files)
            ],
            OrderStates.PHONE: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ],
            OrderStates.NOTES: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_notes)
            ],
            OrderStates.CONFIRM: [
                MessageHandler(filters.Regex(CANCEL_RE), handle_cancel),
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirm)
            ],
            OrderStates.CANCEL_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cancel_choice)
            ],
        },
        fallbacks=[
            # Спец-обработчик только для шага выбора категории
            MessageHandler(filters.Regex(rf"^{BTN_BACK}$"), handle_back_from_categories),

            # ↩️ Назад и ❌ Отмена (если у тебя есть эти хендлеры)
            MessageHandler(filters.Regex(rf"^{NAV_BACK}$"), handle_back),
            MessageHandler(filters.Regex(rf"^{NAV_CANCEL}$"), handle_cancel),
            CallbackQueryHandler(handle_cancel_choice, pattern=r"^(cancel_step|cancel_all)$"),

            # NEW: Обработчик кнопки "Связаться с оператором" в рамках диалога
            CallbackQueryHandler(handle_contact_operator, pattern="^contact_operator$"),

            # /start в любой момент — аккуратный выход в меню
            CommandHandler("start", reset_to_start),

            # любые другие команды внутри разговора — мягко игнорируем
            MessageHandler(filters.COMMAND, unknown_command_during_flow),
        ],
        name="order", persistent=False, allow_reentry=True
    )
    app.add_handler(conv)
    # Роутер главного меню (группа 0 - до ConversationHandler)
    app.add_handler(MessageHandler(filters.Regex(f"^{BTN_NEW_ORDER}$|^{BTN_MY_ORDERS}$|^{BTN_CALL_OPERATOR}$|^{BTN_HELP}$"), main_menu_router), group=0)
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("call_operator", call_operator_command))
    # Операторская команда: все активные заказы (работает только в операторском чате и для операторов)
    app.add_handler(CommandHandler("all_orders", all_orders))
    app.add_handler(CallbackQueryHandler(on_admin_callback, pattern=r"^(adm_page|adm_open):"))
    app.add_handler(CallbackQueryHandler(handle_status_callback, pattern=r"^(take_order_|start_work_|complete_order_)"))
    # Глобальный просмотр заказа по коду из любого состояния
    app.add_handler(CallbackQueryHandler(cb_view_order, pattern=r"^order_view:"))
    # Обработчик контактов оператора
    app.add_handler(CallbackQueryHandler(handle_contact_operator, pattern="^contact_operator$"))
    # Прочие коллбэки админки не регистрируем здесь (тихий список без кнопок)
    app.add_error_handler(error_handler)
    
    # Глобальная страховка от падений
    async def global_error_handler(update, context):
        import traceback; print("GLOBAL ERROR:", traceback.format_exc())
        try:
            await eff_msg(update).reply_text("⚠️ Техническая ошибка. Попробуйте ещё раз.")
        except Exception:
            pass
    
    app.add_error_handler(global_error_handler)
    return app

async def build_application():
    """Async factory to build Application for internal stress harness."""
    return create_application()

def main():
    setup_logging()
    if not config.BOT_TOKEN or ":" not in config.BOT_TOKEN:
        print("❌ BOT_TOKEN отсутствует или неверный."); return
    app=create_application()
    print("✅ Bot starting (polling)…")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__=="__main__": main()