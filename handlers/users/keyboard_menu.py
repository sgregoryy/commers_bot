from aiogram import types, F
from loader import dp
from keyboards.inline import inline_kb_menu
from utils.db_api.db_asyncpg import *
from aiogram.utils.deep_linking import create_start_link
from handlers.users.inline_menu import send_basket
from handlers.users.commands import start_menu

@dp.message(F.text.in_(['🗂️ Каталог', 'каталог', "Назад в каталог"]))
async def show_catalog(message: types.Message):
    await message.answer(f'''Вы перешли в каталог, выберите товар:''',
                         reply_markup=await inline_kb_menu.tovar_list_markup())


@dp.message(F.text.in_(['🛍️ Корзина', 'корзина']))
async def show_basket(message: types.Message):
    await send_basket(chat_id=message.chat.id, user_id=message.chat.id)

@dp.message(F.text.in_(['💲 Баланс', 'баланс']))
async def show_balance(message: types.Message):
    balance = await get_user_balance(message.from_user.id)
    
    # Создаем InlineKeyboardMarkup и добавляем в него кнопки
    btn = [types.InlineKeyboardButton(text='К товарам', callback_data='categories'), types.InlineKeyboardButton(text='Пополнить', callback_data='pay')]
    markup = types.InlineKeyboardMarkup(inline_keyboard=[btn])  # Можно указать row_width для управления количеством кнопок в строке
    
    # Отправляем сообщение с разметкой
    await message.answer(f"{message.from_user.full_name}, на вашем балансе: \n{balance:.2f}💲",
                         reply_markup=markup)