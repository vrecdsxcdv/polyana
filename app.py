"""
Главный файл приложения бота типографии.
"""

import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, Defaults, ApplicationBuilder
)

# Загружаем переменные окружения из .env файла
load_dotenv()

from config import config
from database import create_tables
from states import OrderStates
from handlers.common import start_command, help_command, call_operator_command, error_handler, my_orders_open, my_orders_cb
from handlers.menu_handlers import handle_my_orders, handle_new_order, handle_contact_operator, handle_help
from handlers.order_flow import (
    start_order, handle_product, handle_bc_qty, handle_bc_size, handle_bc_sides,
    handle_fly_format, handle_fly_sides, handle_upload, handle_due,
    handle_phone, handle_notes, handle_confirm, handle_back,
    handle_sheet_format, handle_custom_size, handle_postpress, handle_postpress_bigovka,
    handle_cancel_choice, handle_cancel, handle_print_format, handle_print_type,
    handle_print_format_new, handle_print_type_new, handle_postpress_new,
    handle_smart_cancel, handle_cancel_choice_new,
    BACK_RE, NEXT_RE, SKIP_RE, SUBMIT_RE
)
from handlers.operator import get_operator_handlers
from handlers.status import status_command, status_callback
from handlers.admin import get_admin_handlers


def setup_logging() -> None:
    """Настраивает логирование с ротацией."""
    import logging.handlers
    
    # Настраиваем ротацию логов
    file_handler = logging.handlers.RotatingFileHandler(
        "bot.log", 
        maxBytes=1_000_000,  # 1 МБ
        backupCount=3
    )
    
    # Форматтер для логов
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    
    # Консольный вывод
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


def create_application() -> Application:
    """Создает и настраивает приложение бота."""
    # Создаем приложение с Defaults и таймаутами
    defaults = Defaults(tzinfo=config.TIMEZONE, parse_mode="HTML")
    application = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .defaults(defaults)
        .get_updates_connection_pool_size(4)
        .read_timeout(10)
        .connect_timeout(10)
        .pool_timeout(5)
        .build()
    )
    
    # Создаем таблицы в базе данных
    create_tables()
    
    # Conversation handler для диалога заказа
    order_conversation = ConversationHandler(
        entry_points=[
            CommandHandler("neworder", start_order),
            MessageHandler(filters.Regex("^📝 Новый заказ$"), start_order)
        ],
        states={
            OrderStates.PRODUCT: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product)
            ],
            OrderStates.BC_QTY: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bc_qty)
            ],
            OrderStates.BC_SIZE: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bc_size)
            ],
            OrderStates.BC_SIDES: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bc_sides)
            ],
            OrderStates.FLY_FORMAT: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fly_format)
            ],
            OrderStates.FLY_SIDES: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fly_sides)
            ],
            # Новые состояния
            OrderStates.ORDER_SHEET_FORMAT: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sheet_format)
            ],
            OrderStates.ORDER_CUSTOM_SIZE: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_size)
            ],
            OrderStates.ORDER_POSTPRESS: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_postpress)
            ],
            OrderStates.ORDER_POSTPRESS_BIGOVKA: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_postpress_bigovka)
            ],
            OrderStates.CANCEL_CHOICE: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cancel_choice)
            ],
            OrderStates.PRINT_FORMAT: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_print_format)
            ],
            OrderStates.PRINT_TYPE: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_print_type_new)
            ],
            OrderStates.POSTPRESS: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_postpress_new)
            ],
            OrderStates.ORDER_UPLOAD: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.Document.ALL, handle_upload),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_upload)
            ],
            OrderStates.ORDER_DUE: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_due)
            ],
            OrderStates.ORDER_PHONE: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ],
            OrderStates.ORDER_NOTES: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_notes)
            ],
            OrderStates.ORDER_CONFIRM: [
                MessageHandler(filters.Regex(BACK_RE), handle_back),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirm)
            ]
        },
        fallbacks=[
            MessageHandler(filters.Regex(BACK_RE), handle_back),
            MessageHandler(filters.Regex("^❌ Отмена$"), handle_cancel)
        ],
        name="order_conversation",
        persistent=False,
        allow_reentry=True
    )
    
    # Добавляем обработчики
    application.add_handler(order_conversation)
    
    # Основные команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CommandHandler("call_operator", call_operator_command))
    application.add_handler(CommandHandler("neworder", start_order))
    application.add_handler(CommandHandler("status", my_orders_open))
    
    # Кнопки главного меню
    application.add_handler(MessageHandler(filters.Regex("^🆕 Новый заказ$"), handle_new_order))
    application.add_handler(MessageHandler(filters.Regex("^📦 Мои заказы$"), handle_my_orders))
    application.add_handler(MessageHandler(filters.Regex("^☎️ Связаться с оператором$"), handle_contact_operator))
    application.add_handler(MessageHandler(filters.Regex("^❓ Помощь$"), handle_help))
    
    # Коллбэки списка заказов
    application.add_handler(CallbackQueryHandler(my_orders_cb, pattern="^ord:"))
    application.add_handler(CommandHandler("status", status_command))
    
    # Обработчики для операторов
    for h in get_operator_handlers():
        application.add_handler(h)

    # Пагинация статусов
    application.add_handler(CallbackQueryHandler(status_callback, pattern=r"^status:\d+$"))
    
    # Административные команды
    for handler in get_admin_handlers():
        application.add_handler(handler)
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    return application


def main() -> None:
    """Главная функция запуска бота."""
    # Настраиваем логирование
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Запуск бота типографии...")
    
    # Проверяем токен бота
    if not config.BOT_TOKEN:
        error_msg = "❌ ОШИБКА: BOT_TOKEN не найден в переменных окружения!"
        logger.error(error_msg)
        print(error_msg)
        print("💡 Убедитесь, что файл .env существует и содержит BOT_TOKEN")
        return
    
    if len(config.BOT_TOKEN.split(':')) != 2:
        error_msg = "❌ ОШИБКА: Неверный формат BOT_TOKEN!"
        logger.error(error_msg)
        print(error_msg)
        print("💡 Токен должен быть в формате: 123456:ABC-DEF1234ghIkl-zyx57W2v1u1234")
        return
    
    try:
        # Создаем приложение
        application = create_application()
        
        # Выводим информацию о запуске
        logger.info("✅ Bot started (polling). Username: @SendPrintBot")
        print("✅ Bot started (polling). Username: @SendPrintBot")
        print(f"📁 DB: ./bot.db")
        print(f"📁 Uploads: ./uploads/")
        
        # Запускаем бота
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    main()