import os, asyncio
from dotenv import load_dotenv
from telegram import Bot, BotCommand
load_dotenv(); bot=Bot(os.getenv("BOT_TOKEN"))
async def main():
    cmds=[BotCommand("start","Начать"),BotCommand("help","Помощь"),
          BotCommand("neworder","Новый заказ"),BotCommand("status","Статус заказов"),
          BotCommand("call_operator","Позвать оператора")]
    await bot.set_my_commands(cmds)
    me=await bot.get_me()
    print(f"✅ Команды установлены для @{me.username}")
asyncio.run(main())