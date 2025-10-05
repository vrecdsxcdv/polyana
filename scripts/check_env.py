import os
import asyncio
from dotenv import load_dotenv
from telegram.ext import Application

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не задан в .env")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()

    # Получаем необработанные апдейты
    updates = await app.bot.get_updates()
    if not updates:
        print("ℹ️ Нет новых апдейтов. Напишите сообщение в нужной группе и запустите скрипт снова.")
    else:
        printed = set()
        for u in updates:
            msg = getattr(u, "message", None) or getattr(u, "channel_post", None)
            if not msg:
                continue
            chat = msg.chat
            if chat and chat.id not in printed:
                title = chat.title or chat.full_name or str(chat.id)
                print(f"📌 Чат: {title}\nchat_id = {chat.id}\n")
                printed.add(chat.id)

    await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())