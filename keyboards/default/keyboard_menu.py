from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


main = ReplyKeyboardMarkup(
    keyboard=[
            [
                KeyboardButton(text='🗂️ Каталог'),
                KeyboardButton(text='🛍️ Корзина'),
                KeyboardButton(text='💲 Баланс')
            ],
        ],
    resize_keyboard=True
)


cancel = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отмена')]],
                             resize_keyboard=True)

without_photo = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Без фото', callback_data='without_photo')]],
                                    resize_keyboard=True)

withoutdesc = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Без описания')]],
                                  resize_keyboard=True)

agreement = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Да')],
                                          [KeyboardButton(text='Нет')]],
                                resize_keyboard=True)

with_out_text = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Без текста')],
                                              [KeyboardButton(text='отмена')]],
                                    resize_keyboard=True)

phone = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Отправить номер телефона 📱', request_contact=True)],
              [KeyboardButton(text='отмена')]],
    resize_keyboard=True
)
