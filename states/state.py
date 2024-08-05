from aiogram.fsm.state import StatesGroup, State

class PriceUpdate(StatesGroup):
    waiting_for_price = State()
    amount = State()

class PromoCodeState(StatesGroup):
    waiting_for_promocodes = State()

class OnAccpetion(StatesGroup):
    list_of_transactions = State()

class CountCodes(StatesGroup):
    count = State()
    amount = State()
    price = State()

class TransactionAccept(StatesGroup):
    accept = State()
    user_id = State()
    operation_id = State()

class Transaction(StatesGroup):
    amount = State()
    operation_id = State()

class ConfirmOrder(StatesGroup):
    msg_list = State()
    callback = State()

    fio = State()
    phone = State()


class AdminSpam(StatesGroup):
    msg_list = State()
    text = State()
    confirm = State()


class Search(StatesGroup):
    msg_list = State()
    tovar_name = State()


class SetCount(StatesGroup):
    msg_list = State()
    tovar_id = State()
    count = State()


class SetCountInBasket(StatesGroup):
    msg_list = State()
    tovar_id = State()
    count = State()


class FSMAdmin(StatesGroup):
    msg_list = State()
    callback = State()

    category_id = State()
    category = State()

    product = State()
    product_price = State()
    product_desc = State()
    product_photo = State()
    product_rating = State()

    agreement = State()


class FSMAdminDelete(StatesGroup):
    msg_list = State()
    callback = State()

    category_id = State()
    category = State()

    product_id = State()
    product = State()


class FSMAdminEdit(StatesGroup):
    msg_list = State()
    callback = State()

    product_id = State()
    category_id = State()
    category = State()

    product = State()
    product_price = State()
    product_desc = State()
    product_photo = State()
    product_rating = State()

    agreement = State()


class AddReview(StatesGroup):
    msg_list = State()

    rating = State()
    review = State()

    confirm = State()