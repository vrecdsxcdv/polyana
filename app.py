import logging, logging.handlers
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters, Defaults
from datetime import timezone
from config import config
from database import create_tables, safe_migrate
from states import OrderStates
from handlers.common import start_command, help_command, error_handler
from handlers.order_flow import (
    start_order, handle_product, handle_bc_qty, handle_bc_size, handle_bc_sides,
    handle_sheet_format, handle_custom_size, handle_postpress, handle_postpress_bigovka,
    handle_banner_size, handle_material, handle_print_color, handle_upload, handle_due,
    handle_phone, handle_notes, handle_confirm, handle_back, handle_cancel, handle_cancel_choice,
    BACK_RE
)

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
        entry_points=[CommandHandler("neworder", start_order), MessageHandler(filters.Regex("^📝 Новый заказ$"), start_order)],
        states={
            OrderStates.PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product)],
            OrderStates.BC_QTY: [MessageHandler(filters.Regex(BACK_RE), handle_back), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bc_qty)],
            OrderStates.BC_SIZE: [MessageHandler(filters.Regex(BACK_RE), handle_back), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bc_size)],
            OrderStates.BC_SIDES:[MessageHandler(filters.Regex(BACK_RE), handle_back), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bc_sides)],
            OrderStates.ORDER_SHEET_FORMAT:[MessageHandler(filters.Regex(BACK_RE), handle_back), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sheet_format)],
            OrderStates.ORDER_CUSTOM_SIZE:[MessageHandler(filters.Regex(BACK_RE), handle_back), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_size)],
            OrderStates.ORDER_POSTPRESS:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_postpress)],
            OrderStates.ORDER_POSTPRESS_BIGOVKA:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_postpress_bigovka)],
            OrderStates.ORDER_BANNER_SIZE:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_banner_size)],
            OrderStates.ORDER_MATERIAL:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_material)],
            OrderStates.ORDER_PRINT_COLOR:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_print_color)],
            OrderStates.ORDER_UPLOAD:[MessageHandler(filters.Document.ALL, handle_upload), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_upload)],
            OrderStates.ORDER_DUE:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_due)],
            OrderStates.ORDER_PHONE:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
            OrderStates.ORDER_NOTES:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_notes)],
            OrderStates.ORDER_CONFIRM:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirm)],
            OrderStates.CANCEL_CHOICE:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cancel_choice)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel)],
        name="order", persistent=False, allow_reentry=True
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_error_handler(error_handler)
    return app

def main():
    setup_logging()
    if not config.BOT_TOKEN or ":" not in config.BOT_TOKEN:
        print("❌ BOT_TOKEN отсутствует или неверный."); return
    app=create_application()
    print("✅ Bot started (polling).")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__=="__main__": main()