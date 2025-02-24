import asyncio
import logging
from aiogram import Bot, Dispatcher
from db import create_table
from handlers import router

API_TOKEN = '7777322204:AAHDBNl5SEJBXNEPFy1r7IhfYddB_DEOzns'

# Запуск процесса поллинга новых апдейтов
async def main():
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO)

    # Объект бота
    bot = Bot(token=API_TOKEN)

    # Диспетчер
    dp = Dispatcher()
    dp.include_router(router)
    
    await create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())