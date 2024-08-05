import datetime
from decimal import Decimal, ROUND_DOWN
from loader import dp
import logging

async def get_admins():
    async with dp['db_pool'].acquire() as connection:
        return await connection.fetch('SELECT user_id FROM users where isadmin=true')


async def add_promo(amount, promo):
    # Получите доступ к пулу соединений
    async with dp['db_pool'].acquire() as connection:
        # Получите цену для указанного количества
        price = await get_price(amount)
        
        # Выполните SQL-запрос для вставки данных
        await connection.execute('''
            INSERT INTO products (tovar, price, amount, status)
            VALUES ($1, $2, $3, $4)
        ''', promo, price, amount, 'Free')

async def get_user_balance(user_id):
    async with dp["db_pool"].acquire() as connection:
        result = await connection.fetchval('SELECT balance FROM users WHERE id = $1', user_id)
        return result

async def update_user_balance(user_id, new_balance):
    async with dp["db_pool"].acquire() as connection:
        await connection.execute('UPDATE users SET balance = $1 WHERE user_id = $2', new_balance, user_id)

async def get_cart_items(user_id):
    async with dp["db_pool"].acquire() as connection:
        result = await connection.fetch('''
            SELECT basket.product_id, basket.count, products.amount, products.price
            FROM basket
            JOIN products ON basket.product_id = products.id
            WHERE basket.user_id = $1
        ''', user_id)
        return [dict(row) for row in result]

async def clear_cart(user_id):
    async with dp["db_pool"].acquire() as connection:
        await connection.execute('DELETE FROM basket WHERE user_id = $1', user_id)

async def get_promo_codes(cart_items):
    promo_codes = []
    for item in cart_items:
        try:
            async with dp["db_pool"].acquire() as connection:
                # Получаем промокоды
                codes = await connection.fetch('''
                    SELECT tovar FROM products WHERE id = $1 LIMIT $2
                ''', item['product_id'], item['count'])
                promo_codes.append({
                    'amount': item['amount'],
                    'codes': [row['tovar'] for row in codes]
                })
                
                # Обновляем статус промокодов на 'Sold'
                result = await connection.fetch(f'''
                    UPDATE "products" SET "status" = 'Sold' WHERE "tovar" = {codes['tovar']}
                ''')
                print(result)
        except Exception as e:
            logging.error(f"Ошибка при обработке продукта с id {item['product_id']}: {e}")
    
    return promo_codes

async def set_sold(cart_items):
    async with dp['db_pool'].acquire() as connection:
        product_ids = [record['product_id'] for record in cart_items]
        if product_ids:
                    await connection.execute(f'''
                        UPDATE "products"
                        SET "status" = 'Sold'
                        WHERE "id" = ANY($1::int[])
                    ''', product_ids)
async def get_all_users_data():
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            query = '''
                        SELECT
                            ROW_NUMBER() OVER (ORDER BY u.user_id) AS row_number,
                            u.user_id,
                            u.fio,
                            CASE
                                WHEN u.isadmin THEN 'Администратор'
                                ELSE 'Пользователь'
                            END AS status
                        FROM
                            users u
            '''
            return await connection.fetch(query)

async def update_price(item_id, new_price):
    async with dp["db_pool"].acquire() as connection:
        await connection.execute('UPDATE prices SET price = $1 WHERE amount = $2', new_price, item_id)
        await connection.execute('UPDATE products SET price = $1 WHERE amount = $2', new_price, item_id)

async def get_all_items():
    async with dp["db_pool"].acquire() as connection:
        rows = await connection.fetch('SELECT id, amount, price FROM prices ORDER BY amount')
        return [dict(row) for row in rows]

async def get_user_balance(user_id):
    async with dp["db_pool"].acquire() as connecetion:
        async with connecetion.transaction():
            value = await connecetion.fetchval(f'SELECT balance FROM "users" WHERE "user_id"={user_id}')
            decimal_val = Decimal(str(value))
            return decimal_val.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        
async def accept_transaction(user_id, operation_id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            # Обновление статуса транзакции
            await connection.execute(f'''
                UPDATE "transactions"
                SET "status" = 'Accepted'
                WHERE "user_id" = {user_id} AND "file_id" = '{operation_id}'
            ''')

            # Обновление баланса пользователя
            await connection.execute(f'''
                UPDATE "users"
                SET "balance" = "balance" + (
                    SELECT "amount"
                    FROM "transactions"
                    WHERE "user_id" = {user_id} AND "file_id" = '{operation_id}'
                )
                WHERE "user_id" = {user_id}
            ''')
async def add_transaction(user_id, amount, operation_id, date=None):
    async with dp["db_pool"].acquire() as connection:
        async with connection.transaction():
            query = '''
                INSERT INTO transactions (user_id, amount, status, date, file_id)
                VALUES ($1, $2, $3, COALESCE($4, CURRENT_TIMESTAMP), $5)
                RETURNING id;
            '''
            await connection.execute(query, user_id, amount, "OnCheck", date, operation_id)

async def get_next_pending_transaction():
    async with dp["db_pool"].acquire() as connection:
        return await connection.fetch("""SELECT "user_id", "amount", "date", "file_id" FROM "transactions" WHERE "status" = 'OnCheck' LIMIT 1""")


async def get_not_accepted_transactions():
    async with dp["db_pool"].acquire() as connection:
        async with connection.transaction():
            return await connection.fetch("""SELECT "user_id", "amount", "date", "file_id" FROM "transactions" WHERE "status" = 'OnCheck' """)

async def active_users_list():
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetch('SELECT * FROM "users"')

async def get_count(amount):
    async with dp["db_pool"].acquire() as connection:
        async with connection.transaction():
            count = await connection.fetchval(f"""SELECT COUNT(*) From "products" WHERE "amount"={amount} AND "status"='Free'""")
            return count
async def get_price(amount):
    async with dp["db_pool"].acquire() as connection:
        async with connection.transaction():
            value = await connection.fetchval(f'SELECT "price" From "prices" WHERE "amount"={amount}')
            # decimal_val = Decimal(str(value))
            # return decimal_val.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            return value

async def get_promos(amount, count):
    async with dp["db_pool"].acquire() as connection:
        async with connection.transaction():
            # Получаем список id товаров
            product_ids = await connection.fetch(f'''
                SELECT "id"
                FROM "products"
                WHERE "amount" = $1 AND "status" = 'Free'
                LIMIT $2
            ''', amount, count)
            
            # Преобразуем результат в список id
            product_ids = [record['id'] for record in product_ids]
            
            # Если есть товары для обновления
            if product_ids:
                await connection.execute(f'''
                    UPDATE "products"
                    SET "status" = 'Basket'
                    WHERE "id" = ANY($1::int[])
                ''', product_ids)
            
            return product_ids
async def user_exists(user_id: int):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            result = await connection.fetchrow(f'SELECT "user_id" FROM "users" WHERE "user_id"={user_id}')
            print(result)
            return result is not None


async def user_info_by_id(user_id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetchrow('SELECT u.*, '
                                             '(SELECT COUNT(*) FROM "users" WHERE "referral" = $1) AS referral_count '
                                             'FROM "users" AS u WHERE "user_id" = $1', user_id)


async def user_is_admin(user_id: int):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            result = await connection.fetchrow('SELECT "isadmin" FROM "users" WHERE "user_id"=$1 AND "isadmin"=True', user_id)
            return result['isadmin']


async def admin_list():
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetch('SELECT "user_id" FROM "users" WHERE "isadmin"=True')


async def add_user(user_id: int, fio: str, referral=None):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            dt = datetime.datetime.now()
            await connection.execute('INSERT INTO "users" ("user_id", "fio", "isadmin", "dt", "balance") '
                                     'VALUES ($1, $2, $3, $4, $5)', user_id, fio, False, dt, 0)


async def user_list():
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetch('SELECT * FROM "users"')


async def category_list():
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetch('SELECT * FROM "categories" ORDER BY "id"')


async def tovars_by_category():
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetch('SELECT * FROM "prices"')


async def search_tovar_by_name(keyword):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetch('SELECT * FROM "products" WHERE LOWER("tovar") LIKE $1 '
                                          'or LOWER("description") LIKE $1', f'%{keyword.lower()}%')


async def tovar_info_by_id(id: int):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetchrow('SELECT * FROM "products" WHERE "id"=$1', id)


async def tovar_favourite_list(user_id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                'SELECT f.user_id, p.* FROM "favourite" f JOIN "products" p ON f."product_id" = p."id" '
                'WHERE f."user_id" = $1', user_id)


async def tovar_is_favourite(product_id, user_id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            result = await connection.fetchrow('SELECT * FROM "favourite" WHERE "product_id"=$1 and "user_id"=$2',
                                               product_id, user_id)

            return result is not None


async def tovar_set_favourite(product_id, user_id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            if await tovar_is_favourite(product_id=product_id, user_id=user_id):
                await tovar_favourite_del(product_id, user_id)
            else:
                await connection.execute('INSERT INTO "favourite" ("product_id", "user_id") VALUES ($1, $2)',
                                         product_id, user_id)


async def tovar_favourite_del(product_id, user_id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('DELETE FROM "favourite" WHERE "product_id" = $1 AND "user_id" = $2',
                                     product_id, user_id)


async def tovar_favourite_clear(user_id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('DELETE FROM "favourite" WHERE "user_id" = $1', user_id)


async def basket_list(user_id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetch('SELECT b."product_id", p."amount", p."price", b."count" '
                                  'FROM "basket" b '
                                  'JOIN "products" p ON b."product_id" = p."id" '
                                  'WHERE b."user_id" = $1', user_id)


async def tovar_add_to_basket(user_id, product_id, count):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            dt = datetime.datetime.now()

            await connection.execute(
                'INSERT INTO "basket" ("user_id", "product_id", "count", "dt") '
                'VALUES ($1, $2, $3, $4) '
                'ON CONFLICT ("user_id", "product_id") DO UPDATE '
                'SET "count" = "basket"."count", "dt" = $4',
                user_id, product_id, count, dt
            )


async def add_history(user_id, total):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            dt = datetime.datetime.now()
            result = await connection.fetchrow('INSERT INTO "history" ("user_id", "dt", "total", "received") '
                                               'VALUES ($1, $2, $3, $4) RETURNING "id"', user_id, dt, total, False)
            return result["id"]


async def del_history(id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('DELETE FROM "history" WHERE "id"=$1', id)


async def set_history_received(id, received=True):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('UPDATE "history" SET "received"=$1 WHERE "id"=$2', received, id)


async def basket_clear(user_id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('DELETE FROM "basket" WHERE "user_id" = $1', user_id)


async def basket_tovar_del(product_id, user_id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('DELETE FROM "basket" WHERE "product_id" = $1 AND "user_id" = $2',
                                     product_id, user_id)


async def basket_tovar_set_count(product_id, count):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetch('UPDATE "basket" SET "count"=$1 WHERE "product_id"=$2', count, product_id)


async def add_category(category):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('INSERT INTO "categories" ("category") VALUES ($1)', category)


async def delete_category_by_id(id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('DELETE FROM "categories" WHERE "id"=$1', id)


async def category_name_by_id(id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            result = await connection.fetchrow('SELECT "category" FROM "categories" WHERE "id"=$1', id)
            return result["category"] if result else None


async def add_tovar(category, price, description, photo, tovar):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            result = await connection.fetchrow(
                """
                INSERT INTO "products" 
                    ("category", "tovar", "photo", "price", "description")
                VALUES 
                    ($1, $2, $3, $4, $5)
                RETURNING "id"
                """,
                category, tovar, photo, price, description
            )
            return result["id"]


async def product_title_by_id(id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            result = await connection.fetchrow('SELECT "tovar" FROM "products" WHERE "id"=$1', id)
            return result["tovar"] if result else None


async def delete_tovar_by_id(id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('DELETE FROM "products" WHERE "id"=$1', id)


async def edit_tovar_photo(id, photo):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('UPDATE "products" SET "photo"=$1 WHERE "id"=$2', photo, id)


async def edit_tovar_title(id, title):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('UPDATE "products" SET "tovar"=$1 WHERE "id"=$2', title, id)


async def edit_tovar_price(id, price):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('UPDATE "products" SET "price"=$1 WHERE "id"=$2', price, id)


async def edit_tovar_description(id, description):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('UPDATE "products" SET "description"=$1 WHERE "id"=$2', description, id)


async def edit_tovar_rating(id, rating):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            await connection.execute('UPDATE "products" SET "rating"=$1 WHERE "id"=$2', rating, id)


async def review_list_by_product_id(product_id):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetch('SELECT * FROM "reviews" WHERE "product_id"=$1 ORDER BY "dt" DESC', product_id)


async def add_review(user_id, product_id, rating, review):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            dt = datetime.datetime.now()
            result = await connection.fetchrow('INSERT INTO "reviews" '
                                               '("user_id", "product_id", "rating", "review", "dt") '
                                               'VALUES ($1, $2, $3, $4, $5) RETURNING "id"',
                                               user_id, product_id, rating, review, dt)
            return result["id"]


async def user_info_by_user_id(user_id: int):
    async with dp['db_pool'].acquire() as connection:
        async with connection.transaction():
            return await connection.fetchrow('SELECT * FROM "users" WHERE "user_id"=$1', user_id)
