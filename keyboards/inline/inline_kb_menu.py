from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from data.config import manager_url
from utils.db_api.db_asyncpg import *


back_to_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back_to_menu')
         ]
    ]
)


admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⚙️ Изменение цен', callback_data='update_prices')],
        [InlineKeyboardButton(text='📢 Транзакции', callback_data='show_next')],
        [InlineKeyboardButton(text='📋 Пользователи', callback_data='admin_all_users_info')],
        [InlineKeyboardButton(text='➕ Добавить промокоды', callback_data='list_for_adding')]

        # [InlineKeyboardButton(text='Назад', callback_data='back_to_menu')]
    ]
)

back_to_admin = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад', callback_data='admin_main_menu')]
])

async def basket_markup(basket):
    btns = []

    # Если корзина пуста, возвращаем клавиатуру с кнопками "Очистить корзину" и "Назад"
    if not basket:
        btns.append([InlineKeyboardButton(text='Очистить корзину', callback_data='clearBasket')])
        btns.append([InlineKeyboardButton(text='Назад', callback_data='categories')])
        return InlineKeyboardMarkup(inline_keyboard=btns)

    # Сгруппировать товары по amount
    grouped_basket = {}
    for tovar in basket:
        product_id, price, amount, count = tovar
        if amount not in grouped_basket:
            grouped_basket[amount] = {'total_price': price, 'total_count': 0, 'product_ids': set()}
        grouped_basket[amount]['total_count'] += count
        grouped_basket[amount]['product_ids'].add(product_id)

    product_ids = set()

    # Создать кнопки для каждого уникального amount
    for amount, values in grouped_basket.items():
        total_price = values['total_price']
        total_count = values['total_count']
        product_ids.update(values['product_ids'])

        # Создать строку кнопок для каждого unique amount

    # Добавить кнопки для очистки корзины и оформления заказа в отдельные строки
    btns.append([InlineKeyboardButton(text='Очистить корзину', callback_data='clearBasket')])
    if product_ids:
        btns.append([InlineKeyboardButton(text='Оплатить', callback_data=f'confirm_order{"_".join(map(str, product_ids))}')])
    btns.append([InlineKeyboardButton(text='Назад', callback_data='categories')])

    return InlineKeyboardMarkup(inline_keyboard=btns)


async def continue_shopping():
    btns = list()
    btns.append([InlineKeyboardButton(text='Продолжить покупки', callback_data='categories')])
    btns.append([InlineKeyboardButton(text='Оформить заказ', callback_data='basket')])
    return InlineKeyboardMarkup(inline_keyboard=btns)


async def adminconfirm(user_id, app_id):
    btns = list()
    btns.append([InlineKeyboardButton(text='✅ Подтвердить', callback_data=f'admin-confirm_1_{user_id}_{app_id}')])
    btns.append([InlineKeyboardButton(text='❌ Отклонить', callback_data=f'admin-confirm_0_{user_id}_{app_id}')])
    return InlineKeyboardMarkup(inline_keyboard=btns)


async def admin_categories_markup(row_count=2):
    print(1)
    categories = await category_list()
    btns = list()
    btn_row = list()

    for i, category in enumerate(categories):
        if i % row_count == 0 and i != 0:
            btns.append(btn_row)
            btn_row = list()
        btn_row.append(InlineKeyboardButton(text=f'{category["category"]}', callback_data=f'admin-category_1_{category["id"]}'))

    if btn_row:
        btns.append(btn_row)

    # btns.append([InlineKeyboardButton(text='⚙️ Добавить категорию', callback_data='AddNewCategory')])
    btns.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='manager_main_menu')])

    return InlineKeyboardMarkup(inline_keyboard=btns)


async def admin_tovar_list_markup(page=1):
    btns = list()
    tovar_list = await tovars_by_category()
    max_on_one_page = 10
    pages = len(tovar_list) // max_on_one_page + 1 if (len(tovar_list) // max_on_one_page) != (len(tovar_list) / max_on_one_page) else len(tovar_list) // max_on_one_page

    for tovar in tovar_list[(page - 1) * max_on_one_page:page * max_on_one_page]:
        btns.append([InlineKeyboardButton(text=f'{tovar["amount"]}', callback_data=f'admin-tovar-info_{page}_{tovar["id"]}_{1}')])

    if pages > 1:
        btns.append([InlineKeyboardButton(text='⬅️', callback_data=f'admin-category_{page - 1 if page - 1 > 0 else pages}_'),
                     InlineKeyboardButton(text=f'{page}', callback_data=f'_'),
                     InlineKeyboardButton(text='➡️', callback_data=f'admin-category_{page + 1 if pages >= page + 1 else 1}_')])

    # btns.append([InlineKeyboardButton(text='⚙️ Добавить товар', callback_data=f'AddNewTovar_{page}_')])
    # btns.append([InlineKeyboardButton(text='⚙️ Удалить категорию', callback_data=f'DeleteCategory_{page}_{category_id}')])
    btns.append([InlineKeyboardButton(text='Изменить цены', callback_data=f'update_prices')])

    btns.append([InlineKeyboardButton(text='⬅️ Назад', callback_data=f'admin_all_categories')])

    return InlineKeyboardMarkup(inline_keyboard=btns)

async def admin_adding_promos(page=1):
    btns = list()
    tovar_list = await tovars_by_category()
    max_on_one_page = 10
    pages = len(tovar_list) // max_on_one_page + 1 if (len(tovar_list) // max_on_one_page) != (len(tovar_list) / max_on_one_page) else len(tovar_list) // max_on_one_page

    for tovar in tovar_list[(page - 1) * max_on_one_page:page * max_on_one_page]:
        btns.append([InlineKeyboardButton(text=f'{tovar["amount"]}', callback_data=f'admin-add-promo_{tovar["amount"]}')])

    if pages > 1:
        btns.append([InlineKeyboardButton(text='⬅️', callback_data=f'admin-category_{page - 1 if page - 1 > 0 else pages}_'),
                     InlineKeyboardButton(text=f'{page}', callback_data=f'_'),
                     InlineKeyboardButton(text='➡️', callback_data=f'admin-category_{page + 1 if pages >= page + 1 else 1}_')])

    btns.append([InlineKeyboardButton(text='⚙️ Добавить товар', callback_data=f'AddNewTovar_{page}_')])
    # btns.append([InlineKeyboardButton(text='⚙️ Удалить категорию', callback_data=f'DeleteCategory_{page}_{category_id}')])
    btns.append([InlineKeyboardButton(text='Изменить цены', callback_data=f'update_prices')])

    btns.append([InlineKeyboardButton(text='⬅️ Назад', callback_data=f'admin_all_categories')])

    return InlineKeyboardMarkup(inline_keyboard=btns)


async def admin_tovar_info_markup(tovar_id, category, page=1):
    btns = list()

    btns.append([InlineKeyboardButton(text='⚙️ Изменить количество', callback_data=f'EditTovarTitle_{page}_{category}_{tovar_id}')])

    btns.append([InlineKeyboardButton(text='⚙️ Цена', callback_data=f'EditTovarPrice_{page}_{category}_{tovar_id}')])
                #  InlineKeyboardButton(text='⚙️ Описание', callback_data=f'EditTovarDesc_{page}_{category}_{tovar_id}')])

    # btns.append([InlineKeyboardButton(text='⚙️ Фото', callback_data=f'EditTovarPhoto_{page}_{category}_{tovar_id}'),
    #              InlineKeyboardButton(text='⚙️ Рейтинг', callback_data=f'EditTovarRating_{page}_{category}_{tovar_id}')])

    btns.append([InlineKeyboardButton(text='⚙️ Удалить товар', callback_data=f'DeleteTovarById_1_{category}_{tovar_id}')])
    btns.append([InlineKeyboardButton(text='⬅️ Назад', callback_data=f'admin-category_{page}_{category}')])

    return InlineKeyboardMarkup(inline_keyboard=btns)

async def tovar_list_markup(page=1):
    btns = list()
    tovar_list = await tovars_by_category()
    max_on_one_page = 10
    pages = len(tovar_list) // max_on_one_page + 1 if (len(tovar_list) // max_on_one_page) != (len(tovar_list) / max_on_one_page) else len(tovar_list) // max_on_one_page

    for tovar in tovar_list[(page - 1) * max_on_one_page:page * max_on_one_page]:
        btns.append([InlineKeyboardButton(text=f'{tovar["amount"]}uc', callback_data=f'tovar-info_{tovar["amount"]}')])

    if pages > 1:
        btns.append([InlineKeyboardButton(text='⬅️', callback_data=f'category_{page - 1 if page - 1 > 0 else pages}_'),
                     InlineKeyboardButton(text=f'{page}', callback_data=f'_'),
                     InlineKeyboardButton(text='➡️', callback_data=f'category_{page + 1 if pages >= page + 1 else 1}_')])

    # btns.append([InlineKeyboardButton(text='⬅️ Назад', callback_data=f'categories')])

    return InlineKeyboardMarkup(inline_keyboard=btns)

# async def categories_markup(row_count=2):
#     categories = await category_list()
#     btns = list()
#     btn_row = list()
#     btns.append([InlineKeyboardButton(text='🔍 Поиск товара', callback_data='SearchTovar')])

#     for i, category in enumerate(categories):
#         if i % row_count == 0 and i != 0:
#             btns.append(btn_row)
#             btn_row = list()
#         btn_row.append(InlineKeyboardButton(text=f'{category["category"]}', callback_data=f'category_1_{category["id"]}'))

#     if btn_row:
#         btns.append(btn_row)

#     btns.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='DeleteMessage')])

#     return InlineKeyboardMarkup(inline_keyboard=btns)





# async def tovar_search_markup(tovars):
#     btns = list()
#     for tovar in tovars:
#         btns.append([InlineKeyboardButton(text=f'{tovar["tovar"]}', callback_data=f'tovar-info_{1}_{tovar["category"]}_{tovar["id"]}_1')])
#     btns.append([InlineKeyboardButton(text='⬅️ Назад', callback_data='categories')])

#     return InlineKeyboardMarkup(inline_keyboard=btns)


async def tovar_info_markup():
    btns = []
    # btns.append([InlineKeyboardButton(text='👩🏻‍💼 Связаться с менеджером', url=manager_url)])

    # favourite_text = "☆ Добавить в избранное"
    # if await tovar_is_favourite(product_id=tovar_id, user_id=user_id):
    #     favourite_text = "⭐ Убрать из избранного"
    # btns.append([InlineKeyboardButton(text=favourite_text, callback_data=f'setFavourite_{page}_{category_id}_{tovar_id}_{count}')])
    # btns.append([InlineKeyboardButton(text='🌟 Отзывы', callback_data=f'reviews/0/_1_{tovar_id}')])
    # print(count, amount)
    # btns.append([InlineKeyboardButton(text=f'➖', callback_data=f'tovar-counter_{amount}_{count}_minus'),
    #              InlineKeyboardButton(text=f'{count}', callback_data='counter'),
    #              InlineKeyboardButton(text=f'➕', callback_data=f'tovar-counter_{amount}_{count}_plus')])

    # navigation_row = [
    #     InlineKeyboardButton(text='⬅️',
    #                          callback_data=f'tovar-info_{page - 1 if page - 1 > 0 else pages}_{category_id}_{prev_tovar_id}_{1}') if prev_tovar_id is not None else None,
    #     InlineKeyboardButton(text='➡️',
    #                          callback_data=f'tovar-info_{page + 1 if pages >= page + 1 else 1}_{category_id}_{next_tovar_id}_{1}') if next_tovar_id is not None else None
    # ]

    # navigation_row = [btn for btn in navigation_row if btn is not None]

    # btns.append([InlineKeyboardButton(text='🛒 Добавить в корзину', callback_data=f'basketAdd_{amount}_{count}')])
    # if navigation_row and pages > 1:
    #     btns.append(navigation_row)
    btns.append([InlineKeyboardButton(text='💲Приобрести', callback_data=f'addingToBasket')])
    btns.append([InlineKeyboardButton(text='⬅️ Назад', callback_data=f'categories')])

    return InlineKeyboardMarkup(inline_keyboard=btns)

async def confirm_basket(amount, count):
    btns = []
    # btns.append([InlineKeyboardButton(text='👩🏻‍💼 Связаться с менеджером', url=manager_url)])

    # favourite_text = "☆ Добавить в избранное"
    # if await tovar_is_favourite(product_id=tovar_id, user_id=user_id):
    #     favourite_text = "⭐ Убрать из избранного"
    # btns.append([InlineKeyboardButton(text=favourite_text, callback_data=f'setFavourite_{page}_{category_id}_{tovar_id}_{count}')])
    # btns.append([InlineKeyboardButton(text='🌟 Отзывы', callback_data=f'reviews/0/_1_{tovar_id}')])
    # print(count, amount)
    # btns.append([InlineKeyboardButton(text=f'➖', callback_data=f'tovar-counter_{amount}_{count}_minus'),
    #              InlineKeyboardButton(text=f'{count}', callback_data='counter'),
    #              InlineKeyboardButton(text=f'➕', callback_data=f'tovar-counter_{amount}_{count}_plus')])

    # navigation_row = [
    #     InlineKeyboardButton(text='⬅️',
    #                          callback_data=f'tovar-info_{page - 1 if page - 1 > 0 else pages}_{category_id}_{prev_tovar_id}_{1}') if prev_tovar_id is not None else None,
    #     InlineKeyboardButton(text='➡️',
    #                          callback_data=f'tovar-info_{page + 1 if pages >= page + 1 else 1}_{category_id}_{next_tovar_id}_{1}') if next_tovar_id is not None else None
    # ]

    # navigation_row = [btn for btn in navigation_row if btn is not None]

    btns.append([InlineKeyboardButton(text='🛒 Добавить в корзину', callback_data=f'basketAdd_{count}_{amount}')])
    # if navigation_row and pages > 1:
    #     btns.append(navigation_row)

    btns.append([InlineKeyboardButton(text='⬅️ Назад', callback_data=f'categories')])

    return InlineKeyboardMarkup(inline_keyboard=btns)


# async def favourite_markup(user_id):
#     tovar_list = await tovar_favourite_list(user_id)
#     btns = list()
#     for tovar in tovar_list:
#         btns.append([InlineKeyboardButton(text=f'{tovar["tovar"]}', callback_data=f'tovar_1_{tovar["category"]}_{tovar["id"]}_{1}'),
#                     InlineKeyboardButton(text='Убрать', callback_data=f'delFavourite_{tovar["id"]}')])
#     if len(tovar_list) > 0:
#         btns.append([InlineKeyboardButton(text='Очистить список избранного', callback_data='clearFavourite')])
#     btns.append([InlineKeyboardButton(text='Назад', callback_data='back_to_menu')])
#     return InlineKeyboardMarkup(inline_keyboard=btns)





# async def review_markup(page, pages, product_id):
#     btns = list()
#     btns.append([InlineKeyboardButton(text='➕ Оставить отзыв', callback_data=f'add-review/1/_{page}_{product_id}')])

#     navigation_row = [
#         InlineKeyboardButton(text='⬅️', callback_data=f'reviews/1/_{page - 1 if page - 1 > 0 else pages}_{product_id}'),
#         InlineKeyboardButton(text=f'{page}', callback_data='_'),
#         InlineKeyboardButton(text='➡️', callback_data=f'reviews/1/_{page + 1 if pages >= page + 1 else 1}_{product_id}')
#     ]
#     if navigation_row and pages > 1:
#         btns.append(navigation_row)
#     btns.append([InlineKeyboardButton(text='Назад', callback_data='DeleteMessage')])

#     return InlineKeyboardMarkup(inline_keyboard=btns)
