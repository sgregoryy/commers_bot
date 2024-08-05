from loader import dp, bot
from keyboards.default import keyboard_menu
from keyboards.inline import inline_kb_menu
from aiogram import types, F
from aiogram.types import InputFile, FSInputFile
from aiogram.utils.markdown import hlink
import os
import asyncio
import pandas as pd
import openpyxl
from aiogram.fsm.context import FSMContext
from states.state import AdminSpam, FSMAdmin, FSMAdminDelete, FSMAdminEdit, TransactionAccept, OnAccpetion, PriceUpdate, PromoCodeState
from utils.db_api.db_asyncpg import *


async def tovar_info_text(amount, price, count):
    decimal_val = str(price)
    print(price)
    price = decimal_val[0:4]
    msg_text = (f'<b>Промокоды на {amount}uc</b>'
                f'\n\n<b>Цена</b>: <code>{price} $</code>'
                f'\n\n<b>Количество</b>:\n<code>{count}</code>')
    return msg_text


async def delete_messages(messages, chat_id):
    for msg_id in messages:
        try:
            await dp.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except:
            pass


async def try_delete_call(call: types.CallbackQuery):
    try:
        await call.message.delete()
    except:
        pass


async def try_delete_msg(chatId, msgId):
    try:
        await dp.bot.delete_message(chat_id=chatId, message_id=msgId)
    except:
        pass


async def try_edit_call(callback, text, markup):
    try:
        msg = await callback.message.edit_text(text=text, parse_mode='HTML', reply_markup=markup)
    except:
        await try_delete_call(callback)
        msg = await callback.message.answer(text=text, parse_mode='HTML', reply_markup=markup)
    return msg


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
    
@dp.message(F.text=='/admin')
async def adminPanel(messsage: types.Message):
    if await user_is_admin(messsage.from_user.id):
        await messsage.answer(f'Здравствуйте, {messsage.from_user.full_name},  вы попали в админ панель!',
                          reply_markup=inline_kb_menu.admin)
        
@dp.callback_query(F.data == 'admin_menu')
async def adminPanel(call: types.CallbackQuery):
    await try_edit_call(callback=call, text=f'Вы попали в админ панель!', markup=inline_kb_menu.admin)
    # await call.message.answer(f'Вы попали в админ панель!',
    #                     reply_markup=inline_kb_menu.admin)
    await call.answer()

@dp.callback_query(F.data == 'admin_all_packs')
async def adminPacks(call: types.CallbackQuery):
    await try_edit_call(call, text='Выберите пак для редактирования: ', markup=await inline_kb_menu.admin_tovar_list_markup())
    # await call.message.answer(, reply_markup= )
    await call.answer()

@dp.callback_query(F.data == 'list_for_adding')
async def hanndle_adding_list(call: types.CallbackQuery):
    await call.message.answer('Выберите пак для добавления:', reply_markup=await inline_kb_menu.admin_adding_promos())
    await call.answer()
    
@dp.callback_query(F.data == 'show_next')
async def show_next_transaction(call: types.CallbackQuery, state: FSMContext):
    transaction = await get_next_pending_transaction()
    await try_delete_call(call)
    
    await state.set_state(TransactionAccept.user_id)
    if transaction:
        transaction = transaction[0]
        user = await bot.get_chat_member(user_id=transaction["user_id"], chat_id=transaction['user_id'])

        text = (
            f"Пользователь: @{user.user.username}\n"
            f"Сумма: {transaction['amount']}\n"
            f"Дата: {transaction['date']}\n"
        )
        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Показать следующую", callback_data='show_next')],
            [types.InlineKeyboardButton(text="Подтвердить перевод", callback_data="accept_transaction"), 
             types.InlineKeyboardButton(text='Отклонить перевод', callback_data=f'decline_transaction_{transaction['user_id']}')],
        ])
        try:
            await call.message.answer_photo( photo=transaction['file_id'], caption=text, reply_markup=markup)
        except:
            await call.message.answer(text, reply_markup=markup)

        await state.update_data({'user_id': transaction["user_id"], 'operation_id': transaction['file_id'], 'amount': transaction['amount']})
        await state.set_state(TransactionAccept.accept)
        await call.answer()

    else:
        await call.message.answer("Нет ожидающих подтверждения транзакций.", reply_markup=types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='Назад', callback_data='admin_menu')]
        ]))
        await call.answer()

@dp.callback_query(F.data.contains('decline_transaction'))
async def handle_decline(call: types.CallbackQuery):
    user_id = call.data.split('_')[2]
    await bot.send_message(user_id, 'Ваше пополнение было отклонено.')
    await call.answer()

@dp.callback_query(F.data == 'accept_transaction', TransactionAccept.accept)
async def accept_transaction_admin(call: types.CallbackQuery, state: FSMContext):
    await state.update_data({"accept": "Accepted"})
    data = await state.get_data()
    print(data)
    await accept_transaction(data["user_id"], data["operation_id"])
    await state.clear()
    await bot.send_message(chat_id=data['user_id'], text=f"Пополнение одобрено! Сумма: <code>{data['amount']} USDT </code>", parse_mode='HTML')
    
    # Удалить сообщение администратора через 3 секунды
    await asyncio.sleep(3)
    await try_delete_call(call)
    
    await call.answer()
    
    # Fetch and show the next pending transaction after accepting
    await show_next_transaction(call, state)

@dp.callback_query(F.data=='admin_all_users_info')
async def admin_all_users_info(call: types.CallbackQuery):
    print(1)
    if True:
        # await try_delete_call(call=call)
        print(2)
        msg = await call.message.answer('Подождите, файл формируется...')

        users = await get_all_users_data()
        df = pd.DataFrame(users, columns=['№', "Telegram id", "ФИО", "Статус"])

        # Имя файла
        filename = 'Users_Info.xlsx'

        # Сохранение файла локально
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Users Info')
            worksheet = writer.sheets['Users Info']

            for idx, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.column_dimensions[openpyxl.utils.get_column_letter(idx + 1)].width = max_len
            print(4)

        # Отправка файла пользователю
        await call.message.answer_document(document=FSInputFile(filename), reply_markup=inline_kb_menu.back_to_admin)
        print(5)

        # Удаление локально сохраненного файла
        os.remove(filename)
        await call.answer()

@dp.callback_query(F.data == 'update_prices')
async def start_price_update(call: types.CallbackQuery, state: FSMContext):
    items = await get_all_items()
    await state.update_data(items=items, current_index=0)
    await ask_next_price(call.message, state)
    await call.answer()

async def ask_next_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    items = data['items']
    current_index = data['current_index']
    if current_index < len(items):
        item = items[current_index]
        decimal_val = Decimal(str(item['price']))
        price = decimal_val.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        await message.answer(f"Введите цену для пака {item['amount']}uc (старая цена - {price}$):")
        
        await state.set_state(PriceUpdate.waiting_for_price)
    else:
        await message.answer("Цены всех товаров успешно обновлены.")
        await state.clear()

@dp.message(PriceUpdate.waiting_for_price, F.text.in_(['отмена', 'Отмена']))
async def handle_cancel(message: types.Message, state: FSMContext):
    await try_delete_msg(message.chat.id, message.message_id)
    await message.answer('Изменение цен отменено!', reply_markup=types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='В меню', callback_data='admin_menu')]
        ]))
    await state.clear()
@dp.message(PriceUpdate.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    new_price = message.text
    
    if not await digit_check(new_price):
        await message.answer("Введите корректную цену (положительное число):")
        return
    new_price = float(new_price)
    
    data = await state.get_data()
    items = data['items']
    current_index = data['current_index']
    item = items[current_index]
    
    await update_price(item['amount'], new_price)
    
    await state.update_data(current_index=current_index + 1)
    await ask_next_price(message, state)


# Команда /start
@dp.callback_query(F.data.contains('admin-add-promo'))
async def handle_adding_start(call: types.CallbackQuery, state: FSMContext):
    amount = int(call.data.split('_')[1])
    await state.update_data( { "amount": amount })
    await state.set_state(PromoCodeState.waiting_for_promocodes)
    await call.message.answer("Отправьте промокоды. Каждый промокод должен быть в отдельной строке. Когда закончите, напишите 'Готово'.")
    await call.answer()

# Хендлер для получения промокодов
@dp.message(PromoCodeState.waiting_for_promocodes)
async def handle_promocodes(message: types.Message, state: FSMContext):
    # Если пользователь написал 'Готово', завершаем сбор промокодов
    if message.text.strip().lower() == 'готово':
        await message.reply("Промокоды собраны.", reply_markup=types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='В меню', callback_data='admin_menu')]
        ]))
        await state.clear()
        return
    data = await state.get_data()
    # Получаем промокоды из сообщения, разделенные строками
    promocodes = message.text.split('\n')
    for promo in promocodes:
        await add_promo(int(data['amount']), promo)

    await message.reply("Промокоды добавлены. Если у вас есть еще промокоды, отправьте их. Если все, напишите 'Готово'.")

# Хендлер для обработки команды /cancel
@dp.message(F.text.in_(['готово', 'Готово']), PromoCodeState.waiting_for_promocodes)
async def cancel_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.reply("Сбор промокодов отменен.", reply_markup=types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='В меню', callback_data='admin_menu')]
        ]
    ))
