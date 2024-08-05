from data.config import username, password, database, host
from utils.set_bot_commands import set_default_commands
from handlers import dp
from loader import bot
import asyncio
import logging
import asyncpg
from datetime import datetime, timedelta

async def clear_expired_basket_items(pool):
    print("Запуск")
    while True:
        print("В цикле")
        await asyncio.sleep(60)  # Проверяем каждые 10 минут
        try:
            async with pool.acquire() as connection:
                async with connection.transaction():
                    expiration_time = datetime.now() - timedelta(minutes=30)
                    logging.info(f'Checking for expired items at {datetime.now()}. Expiration time: {expiration_time}')
                    expired_items = await connection.fetch(
                        'SELECT "product_id" FROM "basket" WHERE "dt" < $1',
                        expiration_time
                    )
                    if expired_items:
                        logging.info(f'Expired items: {expired_items}')
                        await connection.execute('DELETE FROM "basket" WHERE "dt" < $1', expiration_time)
                        for item in expired_items:
                            await connection.execute(
                                'UPDATE "products" SET "status" = \'Free\' WHERE "id" = $1',
                                item["product_id"]
                            )
                        logging.info(f'Cleared expired items at {datetime.now()}')
                        print("Получилось")
                    else:
                        print("Нет записей")
                        logging.info('No expired items found')
        except Exception as e:
            print(e)
            logging.error(f'Error in clear_expired_basket_items: {e}', exc_info=True)

async def on_startup(dp):
    await set_default_commands(dp)  # Установка команд бота
    await create_db_pool(dp)  # Создание пула базы данных
    clear_expired_basket_items(dp['db_pool'])  # Запуск фоновой задачи
    print('success')

async def create_db_pool(dp):
    dp['db_pool'] = await asyncpg.create_pool(
        user=username,
        password=password,
        host=host,
        database=database,
        max_size=100,
    )

async def close_db_pool(dp):
    await dp['db_pool'].close()

async def on_shutdown(dp):
    await dp.storage.close()
    await dp.storage.wait_closed()
    await close_db_pool(dp)  # Закрытие пула базы данных

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_db_pool(dp))
    loop.create_task(clear_expired_basket_items(dp["db_pool"]))
    logging.basicConfig(level=logging.INFO, filename="logs.txt")
    try:
        loop.run_until_complete(dp.start_polling(bot, on_startup=on_startup, on_shutdown=on_shutdown))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
