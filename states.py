from aiogram.fsm.state import State, StatesGroup


class Client(StatesGroup):
    phone = State()
    marketplace = State()
    wb_order = State()
    ozon_order = State()
    custom_data = State()
    other = State()
    defect = State()
    empty_mp = State()
    ozon_yes_no = State()
    ozon_code = State()
    live_chat = State()          # режим живого чата с оператором


class Admin(StatesGroup):
    write_msg = State()