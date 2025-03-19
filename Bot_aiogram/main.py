import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiogram import Dispatcher
import handlers
import help_file
from config import BOT_TOKEN

bot = help_file.bot

async def main():
    print(f"Бот запущен! Токен: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")
    dp = Dispatcher()
    dp.include_routers(handlers.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
