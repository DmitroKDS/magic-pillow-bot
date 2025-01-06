from aiogram.filters import CommandStart
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.functions.create_log import create_log

from mysql.connector.aio import connect
import config

from bot.functions.select_contact import select_contact

main_handler_router = Router()


@main_handler_router.message(CommandStart())
@main_handler_router.message(F.text == "🔙 Почати з початку")
async def start(message: types.Message, state: FSMContext) -> None:
    """
    Start bot, send welcome message

    Command: /start
    """

    await create_log(message, "start")

    contact_id = message.chat.id
    contact = await select_contact(contact_id)
    
    if contact!=None:
        keyboard_buttons = types.ReplyKeyboardMarkup(
            resize_keyboard=True,
            keyboard=[
                [types.KeyboardButton(text="✨ Створити подушку")],
                [types.KeyboardButton(text="💰 Вартість та склад")],
                [types.KeyboardButton(text="🔍 Переглянути приклади")],
                [types.KeyboardButton(text="🔙 Почати з початку")],
            ],
        )

        await message.answer(
            f"""Привіт {contact[0]} !😏 

Хочеш створити унікальну подушку зі своїм дизайном? 
Тоді ти за адресою! Ми робимо круті ростові подушки до 2 метрів! 🛌💥

Завантаж своє фото (чи друга, котика або кумира), і наш бот разом із штучним інтелектом прибере фон, підготує візуалізацію, а ми зробимо подушку твоєї мрії! Все просто і швидко! 🎉

Лише обери бажаний розмір – від 30 см до 2 метрів! ✨""",
            reply_markup=keyboard_buttons
        )

        await state.clear()
    else:
        keyboard_buttons = types.ReplyKeyboardMarkup(
            resize_keyboard=True,
            keyboard=[
                [types.KeyboardButton(text="Завантажити контакт", request_contact=True)]
            ],
        )

        await message.answer(
            """Привіт!
Ми – майстерня улюблених речей MFest! 💥
Давайте почнемо зі знайомства.
Завантажте, будь ласка, контакт для авторизації.""",
            reply_markup=keyboard_buttons
        )


@main_handler_router.message(F.text == "💰 Вартість та склад")
async def about(message: types.Message) -> None:
    """
    About pillow, bot send info about pillow

    Button: Вартість подушки та її склад
    """
    await create_log(message, "about")


    inline_buttons = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='🌟 Створити подушку', callback_data='create_pil')],
            [types.InlineKeyboardButton(text='❓ В мене є питання', callback_data='question_2')]
        ]
    )

    await message.answer(
        """📏 Стандартні розміри:
    • Маленька – 35 см (з більшої сторони) - вартість  грн.
    • Середня – 65 см (з більшої сторони) - вартість  грн.
    • Велика – 100 см (з більшої сторони) - вартість  грн.
    • Найбільша – 150 см (з більшої сторони) - вартість  грн.
    • Гігантська – 200 см (з більшої сторони) - вартість  грн.
    • Індивідуальний розмір –+ 300 грн до найближчого стандартного розміру

🛏 Склад подушки:
    1️⃣ Тканина – габардин: м’яка, приємна на дотик, легко переться.
    2️⃣ Наповнювач – холофайбер високої якості.

🌀 Легко доглядати:
    🌊 Подушку можна прати в пральній машині при 30°. Після прання потрібно висушити подушку і розподіліть холофайбер!""",
        reply_markup=inline_buttons
    )


@main_handler_router.message(F.content_type == "contact")
async def get_contact(message: types.Message, state: FSMContext) -> None:
    """
    Handle when user send a contact

    Button: additional questions pil
    """
    await create_log(message, "get contact")

    contact = message.contact
    
    contact_id = message.chat.id
    phone = contact.phone_number
    first_name = contact.first_name

    async with await connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
        async with await db_connector.cursor() as db_cursor:
            await db_cursor.execute("INSERT INTO contacts(id, name, phone) VALUES (%s, %s, %s)",
                (
                    contact_id,
                    first_name,
                    phone
                )
            )
        await db_connector.commit()

    await start(message, state)