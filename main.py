import logging
import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import tts

async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(tts.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())