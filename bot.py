import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from handlers import user, admin, callback
from database import check_admin_exists

# Настройка логирования
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(callback.router)

    # Проверяем, есть ли хотя бы один админ (для безопасности)
    await check_admin_exists()

    # Запускаем поллинг
    await dp.start_polling(bot)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import check_expired_cashback_and_notify

scheduler = AsyncIOScheduler()
scheduler.add_job(check_expired_cashback_and_notify, 'interval', hours=24)
scheduler.start()

if __name__ == "__main__":
    asyncio.run(main())
