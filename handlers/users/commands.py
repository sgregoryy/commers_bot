from loader import dp, bot
from aiogram import types, F
from aiogram.filters.command import CommandStart
from keyboards.default import keyboard_menu
from utils.db_api.db_asyncpg import *

def extract_unique_code(text):
    return int(text.split()[1]) if len(text.split()) > 1 else None

@dp.message(CommandStart())
async def start_menu(message: types.Message):
    exists = await user_exists(message.from_user.id)
    if not exists:
        referral = None
        unique_code = extract_unique_code(message.text)
        if unique_code and await user_exists(unique_code):
            referral = unique_code

        await add_user(user_id=message.from_user.id,
                       fio=message.from_user.full_name,
                       referral=referral)

    await message.answer(f'👋 Приветствую, {message.from_user.full_name}!'
                         f'\nНажимай на каталог для выбора пака!',
                         reply_markup=keyboard_menu.main)
    await message.delete()
