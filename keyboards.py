from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True
    )


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟣 Wildberries")],
            [KeyboardButton(text="🔵 Ozon")],
            [KeyboardButton(text="❓ У меня другой вопрос")]
        ],
        resize_keyboard=True
    )


def wb_input_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📖 Инструкция")],
            [KeyboardButton(text="🤷 Я не знаю где это посмотреть")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )


def back_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )


def other_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📭 Пришло пустое вложение 😟")],
            [KeyboardButton(text="⚠️ Брак, чужая табличка")],
            [KeyboardButton(text="👨‍💼 Позовите оператора")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )


def live_chat_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔚 Завершить диалог")]
        ],
        resize_keyboard=True
    )


def empty_mp_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟣 Wildberries")],
            [KeyboardButton(text="🔵 Ozon")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )


def yes_no_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, расскажите")],
            [KeyboardButton(text="❌ Нет, оформлю возврат через поддержку")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )


def remove_kb():
    return ReplyKeyboardRemove()


# --- inline для админки ---

def users_inline(users):
    buttons = []
    for u in users:
        uid, uname, phone = u
        label = f"@{uname}" if uname else f"id:{uid}"
        if phone:
            label += f" ({phone})"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"auser_{uid}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def user_actions(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Заявки", callback_data=f"areqs_{uid}")],
        [InlineKeyboardButton(text="✉️ Написать", callback_data=f"awrite_{uid}")],
    ])


def request_actions(rid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟡 В работе", callback_data=f"aset_{rid}_🟡 В работе")],
        [InlineKeyboardButton(text="✅ Завершена", callback_data=f"aset_{rid}_✅ Завершена")],
        [InlineKeyboardButton(text="❌ Отменена", callback_data=f"aset_{rid}_❌ Отменена")],
    ])