import asyncio
from aiogram import Bot, Dispatcher
from main_menu import router
from config import BOT_TOKEN
from services.user_limits_db import init_db
init_db()
from services.analytics_db import init_db
init_db()

bot = Bot(token=BOT_TOKEN)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())