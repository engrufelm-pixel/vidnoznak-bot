import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_GROUP_ID, ADMIN_IDS
from states import Client, Admin
from keyboards import *
from database import *

router = Router()


# ============================================================
#    УТИЛИТА: извлечь user_id из текста где есть 🆔
# ============================================================

def extract_uid(text: str):
    if not text or "🆔" not in text:
        return None
    try:
        part = text.split("🆔")[1]
        digits = ""
        for ch in part.strip():
            if ch.isdigit():
                digits += ch
            elif digits:
                break
        return int(digits) if digits else None
    except (ValueError, IndexError):
        return None


# ============================================================
#    ОТПРАВКА В ГРУППУ (всегда с 🆔)
# ============================================================

async def send_to_group(bot, user, header, original=None):
    await bot.send_message(ADMIN_GROUP_ID, header)

    if original:
        tag = f"📎 от @{user.username or 'без ника'} | 🆔 {user.id}"

        if original.photo:
            await bot.send_photo(ADMIN_GROUP_ID, original.photo[-1].file_id, caption=tag)
        elif original.document:
            await bot.send_document(ADMIN_GROUP_ID, original.document.file_id, caption=tag)
        elif original.text:
            await bot.send_message(ADMIN_GROUP_ID, f"{tag}\n\n{original.text}")


# ============================================================
#    ОТВЕТ МЕНЕДЖЕРА ИЗ ГРУППЫ → КЛИЕНТУ (reply)
# ============================================================

@router.message(F.chat.id == ADMIN_GROUP_ID, F.reply_to_message)
async def manager_reply(message: Message):
    if message.from_user.is_bot:
        return

    search = (message.reply_to_message.text or "") + (message.reply_to_message.caption or "")
    uid = extract_uid(search)

    if not uid:
        await message.reply("❌ Ответьте на сообщение где есть 🆔")
        return

    try:
        if message.photo:
            await message.bot.send_photo(
                uid, message.photo[-1].file_id,
                caption=f"💬 Ответ менеджера:\n\n{message.caption or ''}"
            )
        elif message.document:
            await message.bot.send_document(
                uid, message.document.file_id,
                caption=f"💬 Ответ менеджера:\n\n{message.caption or ''}"
            )
        else:
            await message.bot.send_message(uid, f"💬 Ответ менеджера:\n\n{message.text}")
        await message.reply("✅ Доставлено клиенту")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


# ============================================================
#    ИГНОР ОСТАЛЬНОГО В ГРУППЕ
# ============================================================

@router.message(F.chat.id == ADMIN_GROUP_ID)
async def ignore_group(message: Message):
    pass


# ============================================================
#    АДМИН-ПАНЕЛЬ (только в личке)
# ============================================================

@router.message(Command("admin"), F.chat.type == "private")
async def admin_cmd(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    users = await get_all_users()
    if not users:
        await message.answer("📭 Пока нет клиентов.")
        return
    await message.answer("👥 Список клиентов:", reply_markup=users_inline(users))


@router.callback_query(F.data.startswith("auser_"))
async def admin_user(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔")
        return
    uid = int(callback.data.split("_")[1])
    await callback.message.answer(f"👤 Клиент ID: {uid}", reply_markup=user_actions(uid))
    await callback.answer()


@router.callback_query(F.data.startswith("areqs_"))
async def admin_reqs(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔")
        return
    uid = int(callback.data.split("_")[1])
    reqs = await get_user_requests(uid)
    if not reqs:
        await callback.message.answer("📭 Нет заявок.")
        await callback.answer()
        return
    for r in reqs:
        rid, order, status, created = r
        text = f"🔹 Заявка #{rid}\n📦 {order}\n📊 {status}\n🕐 {created}"
        await callback.message.answer(text, reply_markup=request_actions(rid))
    await callback.answer()


@router.callback_query(F.data.startswith("aset_"))
async def admin_set_status(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔")
        return
    parts = callback.data.split("_", 2)
    rid = int(parts[1])
    status = parts[2]
    await set_status(rid, status)
    await callback.message.answer(f"✅ Статус заявки #{rid} → {status}")
    await callback.answer()


@router.callback_query(F.data.startswith("awrite_"))
async def admin_write(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔")
        return
    uid = int(callback.data.split("_")[1])
    await state.update_data(target_uid=uid)
    await state.set_state(Admin.write_msg)
    await callback.message.answer(f"✏️ Введите сообщение для клиента {uid}:\n/cancel — отмена")
    await callback.answer()


@router.message(Command("cancel"), F.chat.type == "private")
async def cancel_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено")


@router.message(Admin.write_msg, F.chat.type == "private")
async def admin_send(message: Message, state: FSMContext):
    data = await state.get_data()
    uid = data.get("target_uid")
    try:
        await message.bot.send_message(uid, f"💬 Сообщение от менеджера:\n\n{message.text}")
        await message.answer("✅ Отправлено клиенту")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()


# ============================================================
#    НАВИГАЦИЯ
# ============================================================

async def go_main(message, state):
    await state.set_state(Client.marketplace)
    await message.answer("🏠 Выберите маркетплейс:", reply_markup=main_menu())


@router.message(F.text == "⬅️ Назад", F.chat.type == "private")
async def back(message: Message, state: FSMContext):
    current = await state.get_state()
    if current in [Client.wb_order, Client.ozon_order, Client.other]:
        await go_main(message, state)
    elif current == Client.custom_data:
        await go_main(message, state)
    elif current == Client.defect:
        await state.set_state(Client.other)
        await message.answer("Выберите вариант:", reply_markup=other_menu())
    elif current == Client.empty_mp:
        await state.set_state(Client.other)
        await message.answer("Выберите вариант:", reply_markup=other_menu())
    elif current == Client.ozon_yes_no:
        await state.set_state(Client.empty_mp)
        await message.answer("📭 Укажите где был сделан заказ:", reply_markup=empty_mp_kb())
    elif current == Client.ozon_code:
        await state.set_state(Client.ozon_yes_no)
        await message.answer("Рассказать как оформить доставку?", reply_markup=yes_no_kb())
    else:
        await go_main(message, state)


# ============================================================
#    ЗАВЕРШИТЬ ЖИВОЙ ЧАТ
# ============================================================

@router.message(F.text == "🔚 Завершить диалог", F.chat.type == "private")
async def end_live_chat(message: Message, state: FSMContext):
    await go_main(message, state)
    await message.answer("✅ Диалог с оператором завершён.")


# ============================================================
#    СТАРТ
# ============================================================

@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Client.phone)

    text = (
        "👋 Здравствуйте!\n\n"
        "Здесь вы можете передать информацию по своему заказу "
        "или связаться с менеджером.\n\n"
        "📱 Для начала поделитесь номером телефона:"
    )

    if message.from_user.id in ADMIN_IDS:
        text += "\n\n💡 Админ-панель: /admin"

    await message.answer(text, reply_markup=phone_kb())


@router.message(Client.phone, F.contact)
async def got_phone(message: Message, state: FSMContext):
    await save_user(message.from_user.id, message.from_user.username, message.contact.phone_number)
    await go_main(message, state)


# ============================================================
#    WILDBERRIES
# ============================================================

@router.message(Client.marketplace, F.text == "🟣 Wildberries")
async def mp_wb(message: Message, state: FSMContext):
    await state.update_data(mp="wildberries")
    await state.set_state(Client.wb_order)
    await message.answer(
        "📝 Укажите номер сборочного задания (если знаете)\n"
        "либо время оформления заказа и город.\n\n"
        "Если не знаете где посмотреть — нажмите кнопку ниже 👇",
        reply_markup=wb_input_kb()
    )


@router.message(Client.wb_order, F.text.in_(["📖 Инструкция", "🤷 Я не знаю где это посмотреть"]))
async def wb_instruction(message: Message):
    p1 = os.path.join("images", "wb_1.png")
    p2 = os.path.join("images", "wb_2.png")
    media = [
        InputMediaPhoto(
            media=FSInputFile(p1),
            caption="👆 Посмотреть номер можно кликнув на 3 точки рядом со словом «оформлен»."
        ),
        InputMediaPhoto(media=FSInputFile(p2))
    ]
    await message.answer_media_group(media)
    await message.answer("📝 Введите номер или время+город:", reply_markup=wb_input_kb())


@router.message(Client.wb_order)
async def wb_got(message: Message, state: FSMContext):
    await state.update_data(order=message.text)
    await state.set_state(Client.custom_data)
    await message.answer("📎 Приложите данные для нанесения (фото/файл/текст):", reply_markup=back_kb())


# ============================================================
#    OZON
# ============================================================

@router.message(Client.marketplace, F.text == "🔵 Ozon")
async def mp_ozon(message: Message, state: FSMContext):
    await state.update_data(mp="ozon")
    await state.set_state(Client.ozon_order)
    await message.answer("📝 Укажите номер заказа:", reply_markup=back_kb())


@router.message(Client.ozon_order)
async def ozon_got(message: Message, state: FSMContext):
    await state.update_data(order=message.text)
    await state.set_state(Client.custom_data)
    await message.answer("📎 Приложите данные для нанесения (фото/файл/текст):", reply_markup=back_kb())


# ============================================================
#    ДАННЫЕ → МЕНЕДЖЕРУ
# ============================================================

@router.message(Client.custom_data)
async def got_data(message: Message, state: FSMContext):
    data = await state.get_data()
    order = data.get("order", "—")
    mp = data.get("mp", "—")

    await save_request(message.from_user.id, order, message.text or "файл/фото")

    header = (
        f"📩 Новая заявка\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 @{message.from_user.username or 'без ника'}\n"
        f"🆔 {message.from_user.id}\n"
        f"🏪 {mp}\n"
        f"📦 Заказ: {order}\n"
        f"━━━━━━━━━━━━━━━"
    )
    await send_to_group(message.bot, message.from_user, header, message)
    await message.answer("✅ Информация передана менеджеру.\nОжидайте ответ.", reply_markup=main_menu())
    await state.set_state(Client.marketplace)


# ============================================================
#    ДРУГОЙ ВОПРОС
# ============================================================

@router.message(Client.marketplace, F.text == "❓ У меня другой вопрос")
async def other_q(message: Message, state: FSMContext):
    await state.set_state(Client.other)
    await message.answer("Выберите вариант:", reply_markup=other_menu())


# ============================================================
#    ОПЕРАТОР — ЖИВОЙ ЧАТ
# ============================================================

@router.message(F.text.contains("оператор"), F.chat.type == "private")
async def call_op(message: Message, state: FSMContext):
    header = (
        f"🔔 Вызов оператора!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 @{message.from_user.username or 'без ника'}\n"
        f"🆔 {message.from_user.id}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💬 Клиент ждёт ответа. Для ответа — Reply на это сообщение."
    )
    await send_to_group(message.bot, message.from_user, header)

    await state.set_state(Client.live_chat)
    await message.answer(
        "👨‍💼 Менеджер скоро подключится к диалогу.\n\n"
        "💬 Вы можете писать сообщения прямо сейчас — "
        "менеджер увидит их и ответит вам здесь.\n\n"
        "Когда закончите — нажмите кнопку ниже.",
        reply_markup=live_chat_kb()
    )


# ============================================================
#    ЖИВОЙ ЧАТ — сообщения клиента → в группу
# ============================================================

@router.message(Client.live_chat, F.chat.type == "private")
async def live_chat_msg(message: Message):
    tag = f"💬 Сообщение от @{message.from_user.username or 'без ника'} | 🆔 {message.from_user.id}"

    if message.photo:
        await message.bot.send_photo(
            ADMIN_GROUP_ID,
            message.photo[-1].file_id,
            caption=tag
        )
    elif message.document:
        await message.bot.send_document(
            ADMIN_GROUP_ID,
            message.document.file_id,
            caption=tag
        )
    elif message.text:
        await message.bot.send_message(ADMIN_GROUP_ID, f"{tag}\n\n{message.text}")

    await message.answer("📨 Сообщение отправлено менеджеру.")


# ============================================================
#    БРАК
# ============================================================

@router.message(F.text == "⚠️ Брак, чужая табличка", F.chat.type == "private")
async def defect(message: Message, state: FSMContext):
    await state.set_state(Client.defect)
    await message.answer("😔 Опишите ситуацию подробнее. Приложите фото:", reply_markup=back_kb())


@router.message(Client.defect)
async def defect_got(message: Message, state: FSMContext):
    header = (
        f"⚠️ Брак / чужая табличка\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 @{message.from_user.username or 'без ника'}\n"
        f"🆔 {message.from_user.id}\n"
        f"━━━━━━━━━━━━━━━"
    )
    await send_to_group(message.bot, message.from_user, header, message)

    # после брака — сразу живой чат с оператором
    await state.set_state(Client.live_chat)
    await message.answer(
        "✅ Передано менеджеру.\n\n"
        "👨‍💼 Менеджер подключится к диалогу.\n"
        "💬 Можете продолжать писать — всё дойдёт до менеджера.",
        reply_markup=live_chat_kb()
    )


# ============================================================
#    ПУСТОЕ ВЛОЖЕНИЕ
# ============================================================

@router.message(F.text == "📭 Пришло пустое вложение 😟", F.chat.type == "private")
async def empty_start(message: Message, state: FSMContext):
    await state.set_state(Client.empty_mp)
    await message.answer("📭 Где был сделан заказ:", reply_markup=empty_mp_kb())


@router.message(Client.empty_mp, F.text == "🟣 Wildberries")
async def empty_wb(message: Message, state: FSMContext):
    await message.answer(
        "😔 К сожалению, мы ограничены временем на обработку заказа, "
        "поэтому были вынуждены отправить Вам пустое вложение, "
        "не получив от Вас информации.\n\n"
        "📌 Вы можете оформить заказ по браку в ЛК WB, "
        "приложив подтверждающие фотографии.\n\n"
        "✅ Мы одобрим её без необходимости относить в ПВЗ.\n"
        "После этого Вы сможете повторить заказ.",
        reply_markup=main_menu()
    )
    await state.set_state(Client.marketplace)


@router.message(Client.empty_mp, F.text == "🔵 Ozon")
async def empty_ozon(message: Message, state: FSMContext):
    await state.set_state(Client.ozon_yes_no)
    await message.answer(
        "😔 К сожалению, мы ограничены временем на обработку заказа, "
        "поэтому были вынуждены отправить Вам пустое вложение, "
        "не получив от Вас информации.\n\n"
        "📌 Вы можете оформить возврат ЧЕРЕЗ ПОДДЕРЖКУ ОЗОН. "
        "Сделать это сложно, но ВОЗМОЖНО: необходимо добиться, "
        "чтобы в чате ответил оператор — человек. "
        "Автоматически возврат оформить не получится.\n\n"
        "📦 Также мы можем изготовить для Вас табличку и выслать её напрямую, "
        "для этого нужно самостоятельно оформить доставку через приложение Озон.\n\n"
        "Рассказать как это сделать?",
        reply_markup=yes_no_kb()
    )


@router.message(Client.ozon_yes_no, F.text == "✅ Да, расскажите")
async def ozon_yes(message: Message, state: FSMContext):
    await state.set_state(Client.ozon_code)
    path = os.path.join("images", "ozon_delivery.png")
    await message.answer_photo(
        photo=FSInputFile(path),
        caption=(
            "📦 Перейдите в раздел Ozon Доставка:\n\n"
            "📍 Адрес отправления: Москва\n"
            "📍 Адрес получения — свой адрес\n"
            "📞 Телефон отправителя: +79651057490\n"
            "📞 Телефон получателя — свой\n"
            "📐 Размер: A4\n\n"
            "━━━━━━━━━━━━━━━\n"
            "📩 В ответном сообщении пришлите:\n"
            "1️⃣ Код для отправки\n"
            "2️⃣ Данные для нанесения\n"
            "━━━━━━━━━━━━━━━\n\n"
            "💰 Доставку Вам нужно будет оплатить самостоятельно "
            "(мы уже оплатили доставку пустого отправления).\n\n"
            "🔄 В случае повторного отправления по причине брака "
            "мы оформим доставку за свой счёт."
        ),
        reply_markup=back_kb()
    )


@router.message(Client.ozon_yes_no, F.text == "❌ Нет, оформлю возврат через поддержку")
async def ozon_no(message: Message, state: FSMContext):
    await message.answer("👌 Удачи! Если что — /start", reply_markup=main_menu())
    await state.set_state(Client.marketplace)


@router.message(Client.ozon_code)
async def ozon_got_code(message: Message, state: FSMContext):
    header = (
        f"📦 Ozon повторная отправка\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 @{message.from_user.username or 'без ника'}\n"
        f"🆔 {message.from_user.id}\n"
        f"━━━━━━━━━━━━━━━"
    )
    await send_to_group(message.bot, message.from_user, header, message)
    await save_request(message.from_user.id, "Ozon повтор", message.text or "файл")
    await message.answer("✅ Передано менеджеру. Ожидайте.", reply_markup=main_menu())
    await state.set_state(Client.marketplace)