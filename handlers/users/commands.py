from loader import dp, bot
from aiogram import types, F
from aiogram.filters.command import CommandStart
from keyboards.default import keyboard_menu
from utils.db_api.db_asyncpg import *

def extract_unique_code(text):
    return int(text.split()[1]) if len(text.split()) > 1 else None

@dp.message(CommandStart())
async def start_menu(message: types.Message):
    exists = await user_exists("@" + message.from_user.username)
    if not exists:
        await message.answer('Отказано в доступе пользования ботом')
    else:
        if not exists["fio"]:
            await add_user(message.from_user.id, message.from_user.full_name, "@" + message.from_user.username)
        await message.answer(f'👋 Приветствую, {message.from_user.full_name}!'
                            f'\nНажимай на каталог для выбора пака!',
                            reply_markup=keyboard_menu.main)
        await message.delete()
