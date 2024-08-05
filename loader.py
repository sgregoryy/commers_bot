from aiogram import Bot, types, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from data import config


bot = Bot(token=config.BOT_TOKEN)


dp = Dispatcher(storage=MemoryStorage())