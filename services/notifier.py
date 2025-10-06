from texts import LAYOUT_HINT
async def send_order_to_operators(bot, order_summary: str, chat_id: int):
    # Просто шлём текст в чат оператора; файлы доотправляет хендлер загрузки
    await bot.send_message(chat_id=chat_id, text="📦 Новый заказ\n\n"+order_summary)