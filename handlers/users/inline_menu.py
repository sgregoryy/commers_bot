from loader import dp, bot
# from aiogram.utils.markdown import hlink
from data.config import admin_chat
from keyboards.inline import inline_kb_menu
from keyboards.default import keyboard_menu
from aiogram import types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.state import StateFilter
from aiogram.filters.command import CommandStart
from utils.db_api.db_asyncpg import *
from states.state import SetCount, SetCountInBasket, Search, ConfirmOrder, AddReview, CountCodes, Transaction, TransactionAccept
from aiogram.fsm.context import FSMContext
from handlers.users.admin import try_edit_call, try_delete_call, try_delete_msg, delete_messages, tovar_info_text
import os
import pandas as pd
# from handlers.users.commands import start_menu

async def digit_check(digit):
    digit = digit.replace(',', '.')
    try:
        digit = float(digit)
        if digit >= 0:
            return True
        else:
            return False
    except ValueError:
        return False

@dp.callback_query(F.data=='basket')
async def basket_menu(call: types.CallbackQuery):
    # await try_edit_call(call)
    await send_basket(chat_id=call.message.chat.id, user_id=call.from_user.id)
    await try_delete_call(call)
    await call.answer()

@dp.callback_query(F.data=='clearBasket')
async def clearBasket(call: types.CallbackQuery):
    await clear_cart(user_id=call.from_user.id)
    # await send_basket(chat_id=call.message.chat.id, user_id=call.from_user.id)
    await try_edit_call(call, 'Корзина очищена!', None)
    # await call.message.answer()
    await call.answer()

@dp.callback_query(F.data.contains('basketAdd_'))
async def basketAdd_(call: types.CallbackQuery):
    print(call.data)
    ids = await get_promos(int(call.data.split('_')[1]), int(call.data.split('_')[2]))
    for id in ids:
        await tovar_add_to_basket(user_id=int(call.from_user.id), product_id=id,
                                count=1)
    await try_edit_call(call, f'Товар добавлен в корзину 😉', await inline_kb_menu.continue_shopping())

    # await call.message.answer(text=,
    #                           reply_markup=)
    call.answer()

async def send_basket(chat_id, user_id):
    # Получение данных корзины
    basket = await basket_list(user_id)
    
    # Преобразуем записи в список кортежей
    basket = [(record["product_id"], record["price"], record["amount"], record["count"]) for record in basket]
    
    # Группируем товары по amount
    grouped_basket = {}
    
    for tovar in basket:
        product_id, price, amount, count = tovar
        if amount not in grouped_basket:
            grouped_basket[amount] = {'total_price': price, 'total_count': 0}
        grouped_basket[amount]['total_count'] += count
    
    # Генерация строки и подсчет общей суммы
    string = '<b>Корзина.</b>'
    summ = 0
    count = 1
    
    for amount, values in grouped_basket.items():
        total_price = values['total_price']
        total_count = values['total_count']
        
        # Рассчитываем сумму для этого amount
        price_sum = total_price * total_count
        summ += price_sum
        
        string += f'\n\n{count}. «<code>{amount} uc</code>» ' \
                  f'\n\t\t\tЦена: {total_price:.2f} × {total_count} = {price_sum:.2f} $'
        count += 1
    
    string += '\n__________________' + '_' * len(str(summ))
    string += f'\nИтого: {summ:.2f} $'

    # Отправка сообщения
    markup = await inline_kb_menu.basket_markup(basket=basket)
    await bot.send_message(chat_id=chat_id, text=string, reply_markup=markup, parse_mode="HTML")


@dp.callback_query(F.data == 'categories')
async def categories_menu(call: types.CallbackQuery):
    # try_delete_msg(call.message)
    markup = await inline_kb_menu.tovar_list_markup()
    text = 'Вы перешли в каталог, выберите нужный вам пак.'

    await try_edit_call(callback=call, text=text, markup=markup)


# @dp.callback_query(F.data.contains('tovar-counter_'))
# async def tovar_counter(call: types.CallbackQuery):
#     print(call.data)
#     _, amount, data, action = call.data.split('_')
#     amount = int(amount)
#     data = int(data)
#     count = await get_count(amount=amount)
#     new_count = 0
#     # Увеличение/уменьшение счетчика
#     if 'plus' in call.data:
#         new_count = data + 1
#     else:
#         new_count = data-1
#     # new_count = data + 1 if 'plus' in call.data else data - 1
#     new_count = max(new_count, 1)  # Предотвращаем отрицательные значения
#     if new_count == data:
#         await call.answer()
#     if count < new_count:
#         # print('asdads')
#         await call.message.answer('Превышено количество!')
#         await call.answer()
#     else:
#         print(new_count)
#         # Создание новой клавиатуры с обновленным значением счетчика
#         new_markup = await inline_kb_menu.tovar_info_markup()
        
#         # Обновление сообщения с новой разметкой клавиатуры
#         await call.message.edit_reply_markup(reply_markup=new_markup)
#         await call.answer()


@dp.callback_query(F.data.contains('tovar-info_'))
async def tovar_info_menu(call: types.CallbackQuery, state: FSMContext):
    amount = int(call.data.split('_')[1])
    count = await get_count(amount)
    print(type(count))
    price = await get_price(amount)
    if count:
        msg_text = await tovar_info_text(amount=amount, price=price, count=count)
        markup = await inline_kb_menu.tovar_info_markup()

        
        await state.update_data({"amount": amount, "price": price})
        try:
            await try_edit_call(call, msg_text, markup)
            # await call.message.answer(text=msg_text, reply_markup=markup, parse_mode='HTML')

        except Exception as e:
            print(f"Exception occurred: {e}")
            await try_edit_call(callback=call, text=msg_text, markup=markup)
    else:
        await call.answer('Товар больше не доступен!')

@dp.callback_query(F.data == 'addingToBasket')
async def handle_adding(call: types.CallbackQuery, state:FSMContext):
    await state.set_state(CountCodes.count)
    await try_edit_call(call, "Введите количество необходимых кодов:", None)
    # await call.message.answer()
    await call.answer()

@dp.message(CountCodes.count)
async def handle_count(message: types.Message, state: FSMContext):
    await state.update_data({"count": message.text})
    data = await state.get_data()
    count = await get_count(int(data["amount"]))
    
    if int(data["count"]) > count:
        await message.answer("Введено неверное количество!")
        # call = types.CallbackQuery(data=f'tovar-info_{data["amount"]}', message=message)
        msg_txt = await tovar_info_text(amount=data['amount'], count=data['count'], price=data['price'])
        await message.answer(msg_txt, reply_markup=await inline_kb_menu.tovar_info_markup(), parse_mode='HTML')
        state.clear()
    else:
        # Create a mock callback query object
        
        # call = types.CallbackQuery(data=f'tovar-info_{data["amount"]}', message=message)
        await message.answer(f"Выбрано {data['count']} промокодов \nна {data['amount']}uc", reply_markup=await inline_kb_menu.confirm_basket(data['count'], data["amount"]))
        await state.clear()



@dp.callback_query(F.data == 'pay')
async def process_payment(call: types.CallbackQuery, state: FSMContext):
    # Замените 'your_crypto_wallet_id' на реальный ID крипто-кошелька
    crypto_wallet_id = 'your_crypto_wallet_id'

    # Создание кнопок для подтверждения и отмены
    markup = InlineKeyboardMarkup(inline_keyboard=
        [[InlineKeyboardButton(text='Подтвердить перевод', callback_data='confirm_payment')],
        [InlineKeyboardButton(text='Отмена', callback_data='cancel_payment')]
    ])

    # Отправка сообщения с кнопками
    await call.message.edit_text(
        text=f'Для пополнения баланса необходимо выполнить перевод на крипто-кошелек:\n<b>{crypto_wallet_id}</b>\n\n'
             'Пожалуйста, подтвердите перевод или отмените действие.',
        reply_markup=markup,
        parse_mode='HTML'
    )

    # Ответ на запрос
    await call.answer()

# Хендлер для подтверждения перевода
@dp.callback_query(F.data == 'confirm_payment')
async def confirm_payment(call: types.CallbackQuery, state: FSMContext):
    # Извлечение ID крипто-кошелька из callback_data
    _, crypto_wallet_id = call.data.split('_', 1)
    
    # Логика для обработки подтверждения перевода
    # Например, запись в базу данных или уведомление администратора
    # await some_payment_confirmation_logic(crypto_wallet_id)

    # Ответ пользователю
    await state.set_state(Transaction.amount)
    await call.message.edit_text(
        text=f'Введите сумму пополнения в USDT:',
        parse_mode='HTML'
    )
    await call.answer()

@dp.message(Transaction.amount)
async def transaction_amount(message: types.Message, state: FSMContext):
    await state.update_data({ "amount": message.text})
    await message.answer("Отправьте скриншот перевода:")
    await state.set_state(Transaction.operation_id)

@dp.message(Transaction.operation_id)
async def transaction_amount(message: types.Message, state: FSMContext):
    if message.photo:
        print(message.photo[0].file_id)
        await state.update_data({ "operation_id": message.photo[0].file_id })
        data = await state.get_data()
        await message.answer("Ожидайте подтверждения перевода.")
        await state.clear()
        await add_transaction(message.from_user.id, data['amount'], data['operation_id'])
        awaited_transactions = await get_not_accepted_transactions()
        admins_id = await get_admins()
        for admin in admins_id:
            await bot.send_message(chat_id=admin['user_id'], text=f"Новое пополнение! Количество транзакций ожидающих подтверждение — <code><b>{len(awaited_transactions)}</b></code>",
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Показать", callback_data="show_next")]]), parse_mode='HTML')
        
        await state.set_state(TransactionAccept.accept)
        await state.update_data({ "user_id": message.from_user.id, "operation_id": data['operation_id'] })
    # await bot.send_message(chat_id=1054184718, text=f"Пользователь @{message.from_user.username} выполнил перевод \n<b>Cумма:</b> <code>{data["amount"]} </code>\n<b>Id транзакции:</b> <code>{data['operation_id']}</code> \n<b>Время:</b> <code>{datetime.datetime.now()}</code> \nОтправьте любой символ для подтверждения перевода"
    #                        , parse_mode='HTML')
# Хендлер для отмены перевода
@dp.callback_query(F.data == 'cancel_payment')
async def cancel_payment(call: types.CallbackQuery):
    # Логика для обработки отмены перевода
    # Например, удаление сообщения или уведомление администратора
    # await some_payment_cancellation_logic()

    # Ответ пользователю
    await call.message.edit_text(
        text='Перевод был отменен.',
        parse_mode='HTML'
    )
    await call.answer()

@dp.callback_query(F.data.contains('confirm_order'))
async def handle_confirm_order(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    
    # Получение информации о корзине
    cart_items = await get_cart_items(user_id)
    if not cart_items:
        await call.message.answer("Ваша корзина пуста.")
        return
    
    # Расчет общей стоимости
    total_price = sum(item['price'] * item['count'] for item in cart_items)
    
    # Проверка баланса пользователя
    user_balance = await get_user_balance(user_id)
    if user_balance < total_price:
        print(user_balance, total_price)
        await call.message.answer("У вас недостаточно средств на счете.")
        return
    else:
        # Обновление баланса пользователя
        await update_user_balance(user_id, float(user_balance) - total_price)
        
        # Отправка промокодов
        promo_codes = await get_promo_codes(cart_items)
        await set_sold(cart_items=cart_items)
        
        if len(promo_codes) <= 10:
            # Отправка промокодов в сообщении
            promo_codes_text = "\n".join([f"{item['amount']}uc: <code>{code}</code>" for item in promo_codes for code in item['codes']])
            await bot.send_message(user_id, f"Ваши промокоды:\n{promo_codes_text}", parse_mode='HTML')
        else:
            # Сохранение промокодов в Excel файл
            df = pd.DataFrame([{"amount": item['amount'], "code": code} for item in promo_codes for code in item['codes']])
            file_path = f"/tmp/promo_codes_{user_id}.xlsx"
            df.to_excel(file_path, index=False)
            
            # Отправка Excel файла
            file = types.FSInputFile(file_path)
            await bot.send_document(user_id, file, caption="Ваши промокоды:")
            
            # Удаление файла
            os.remove(file_path)
        
        # Очистка корзины
        await clear_cart(user_id)
        
        await call.message.answer("Ваш заказ был успешно обработан.")
        await call.answer()