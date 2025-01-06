from aiogram import Router, types, F
from aiogram.filters import CommandStart, CommandObject

from bot.functions.create_log import create_log

from aiogram.fsm.context import FSMContext
from bot.functions.bot_states import pil_other_count

from bot.functions.create_offer import create_offer_url

from mysql.connector.aio import connect
import config


order_pil_handler_router = Router()


@order_pil_handler_router.callback_query(F.data == 'order_pil')
async def order_pil(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """
    Order pil

    Button: order pil
    """
    await create_log(callback_query.message, "Order pil")

    inline_buttons = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='Гігантська', callback_data='pil_size_200')],
            [types.InlineKeyboardButton(text='Найбільша', callback_data='pil_size_150')],
            [types.InlineKeyboardButton(text='Велика', callback_data='pil_size_100')],
            [types.InlineKeyboardButton(text='Середня', callback_data='pil_size_65')],
            [types.InlineKeyboardButton(text='Маленька', callback_data='pil_size_35')],
            [types.InlineKeyboardButton(text='Хочу свій розмір', callback_data='pil_other_size')]
        ]
    )

    await callback_query.message.answer(
        """🎉 Це зображення ідеально підходить для подушок
Маленька (35 см з більшої сторони) - вартість ? грн
Середня (65 см з більшої сторони) - вартість ? грн
Велика (100 см з більшої сторони) - вартість ? грн
Найбільша (150 см з більшої сторони) - вартість ? грн
Гігантська (200 см з більшої сторони) - вартість ? грн

Який розмір обираєш? 😊""",
        reply_markup=inline_buttons
    )

@order_pil_handler_router.callback_query(F.data == 'pil_other_size')
async def pil_other_size(callback_query: types.CallbackQuery):
    """
    Choose other size

    Button: other size
    """
    await create_log(callback_query.message, "Pil other size")

    inline_buttons = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text=f'{size}', callback_data=f'pil_size_{size}')] for size in range(0, 201, 10)
        ]
    )

    await callback_query.message.answer(
        """Виберіть розмір 😊""",
        reply_markup=inline_buttons
    )


@order_pil_handler_router.callback_query(F.data.contains('pil_size_'))
async def pil_count(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Choose pil count

    Button: pil size
    """
    await create_log(callback_query.message, "Pil count")

    pil_size = int(callback_query.data.split('_')[-1])
    await state.update_data(pil_size=pil_size)

    await callback_query.message.answer(
        f'Ви обрали розмір {pil_size} см. 😊'
    )


    inline_buttons = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='1', callback_data=f'pil_count_1')],
            [types.InlineKeyboardButton(text='2', callback_data=f'pil_count_2')],
            [types.InlineKeyboardButton(text='3', callback_data=f'pil_count_3')],
            [types.InlineKeyboardButton(text='Своя кількість', callback_data=f'pil_other_count')]
        ]
    )

    await callback_query.message.answer(
        """Тепер ведіть кількість яка вам потрібна:""",
        reply_markup=inline_buttons
    )

@order_pil_handler_router.callback_query(F.data == 'pil_other_count')
async def pil_other_count_ask(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Choose custom number

    Button: custom number
    """
    await create_log(callback_query.message, "pil other count ask")

    await callback_query.message.answer(
        """Введіть свою кількість 😊"""
    )

    await state.set_state(pil_other_count.is_waiting)


@order_pil_handler_router.message(
    (F.content_type == "text"),
    pil_other_count.is_waiting
)
@order_pil_handler_router.callback_query(F.data.contains('pil_count_'))
async def pil_other_count_submit(message: types.Message | types.CallbackQuery, state: FSMContext):
    """
    Submit pil other count

    Message: other count
    """
    if not(isinstance(message, types.Message) and message.text.isdigit() and int(message.text) > 0) and not isinstance(message, types.CallbackQuery):
        await message.answer(
            f'Ведіть будь ласка цифру'
        )
        return
    
    if isinstance(message, types.CallbackQuery):
        pil_count = int(message.data.split('_')[-1])
        message = message.message
    else:
        pil_count = int(message.text)

    await create_log(message, "pil count submit")

    pil_size  = (await state.get_data())["pil_size"]
    await state.update_data(pil_size=pil_size, pil_count=pil_count)


    await message.answer(
        f'Ви обрали кількість {pil_count} шт.'
    )


    inline_buttons = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='1️⃣', callback_data=f'pay_method_1')],
            [types.InlineKeyboardButton(text='2️⃣', callback_data=f'pay_method_2')],
            [types.InlineKeyboardButton(text='3️⃣', callback_data=f'pay_method_3')],
        ]
    )

    await message.answer(
        """Ціна цієї подушки — 1000 грн.

Тепер обирай зручний спосіб оплати та доставки:
1️⃣ Повна оплата через систему MonoPay.

2️⃣ Оплата за номером рахунка.

3️⃣ Накладений платіж – сплачуєш лише завдаток у розмірі 300 грн, решту при отриманні.

Обирай свій варіант, і вперед до мрії! 😊💳📦""",
        reply_markup=inline_buttons
    )


@order_pil_handler_router.callback_query(F.data == 'pay_method_1')
async def pay_method_1(callback_query: types.CallbackQuery, state: FSMContext):
    await create_log(callback_query.message, "User have selected pay method 1")
    await callback_query.message.edit_reply_markup(reply_markup=None)

    pil_size  = (await state.get_data())["pil_size"]
    pil_count  = (await state.get_data())["pil_count"]

    contact_id = callback_query.message.chat.id

    async with await connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
        async with await db_connector.cursor() as db_cursor:
            await db_cursor.execute("SELECT request_id FROM requests WHERE contact_id = %s ORDER BY request_id DESC LIMIT 1;",
                (
                    contact_id,
                )
            )
            
            pil_id=await db_cursor.fetchone()
            if pil_id!=None:
                pil_id=pil_id[0]
            else:
                return

    offer_url = await create_offer_url(pil_id, pil_size, pil_count, 1000, pil_count*1000)

    await callback_query.message.answer(
        f"""Давай перейдомо до оплати та вибора способа доставки.
Тицяй ось тут і оплати легко і швидко - {offer_url}"""
    )

    await state.clear()

    
    async with await connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
        async with await db_connector.cursor() as db_cursor:
            await db_cursor.execute(
                """
                INSERT INTO orders(order_id, pil_size, pil_count, status)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    pil_id,
                    pil_size,
                    pil_count,
                    "not confirmed"
                )
            )   
        await db_connector.commit()


@order_pil_handler_router.callback_query(F.data == 'pay_method_2')
async def pay_method_2(callback_query: types.CallbackQuery, state: FSMContext):
    await create_log(callback_query.message, "User have selected pay method 2")
    await callback_query.message.edit_reply_markup(reply_markup=None)

    pil_size  = (await state.get_data())["pil_size"]
    pil_count  = (await state.get_data())["pil_count"]


    contact_id = callback_query.message.chat.id

    async with await connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
        async with await db_connector.cursor() as db_cursor:
            await db_cursor.execute("SELECT request_id FROM requests WHERE contact_id = %s ORDER BY request_id DESC LIMIT 1;",
                (
                    contact_id,
                )
            )
            
            pil_id=await db_cursor.fetchone()
            if pil_id!=None:
                pil_id=pil_id[0]
            else:
                return


    await callback_query.message.answer(
        f"""Для сплати замовлення, перейдить в ваш банківський додаток. Оберіть "Платежі" і скопіюйте ось цей номер нашого банківського Рахунку (IBAN)
UA873354960000026007051605770

Більшість банків, підтягує автоматом всі інші потрібні реквізити, а саме ЄДРПОУ: 3019203120
та назва ФОП: ФОП Кривулянська С. M.
та вам залишилось вказати суму оплати та на самом кінці в Призначенні платежу вказати:Оплата за замовлення {(8-len(f'{pil_id}'))*"0"+f'{pil_id}'}"""
    )

    await state.clear()
    
    
    async with await connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
        async with await db_connector.cursor() as db_cursor:
            await db_cursor.execute(
                """
                INSERT INTO orders(order_id, pil_size, pil_count, status)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    pil_id,
                    pil_size,
                    pil_count,
                    "requires confirmation"
                )
            ) 
        await db_connector.commit()


@order_pil_handler_router.callback_query(F.data == 'pay_method_3')
async def pay_method_3(callback_query: types.CallbackQuery, state: FSMContext):
    await create_log(callback_query.message, "User have selected pay method 3")

    pil_size  = (await state.get_data())["pil_size"]
    pil_count  = (await state.get_data())["pil_count"]

    contact_id = callback_query.message.chat.id

    async with await connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
        async with await db_connector.cursor() as db_cursor:
            await db_cursor.execute("SELECT request_id FROM requests WHERE contact_id = %s ORDER BY request_id DESC LIMIT 1;",
                (
                    contact_id,
                )
            )
            
            pil_id=await db_cursor.fetchone()
            if pil_id!=None:
                pil_id=pil_id[0]
            else:
                return

    offer_url = await create_offer_url(pil_id, pil_size, pil_count, 1000, 300)

    await callback_query.message.answer(
        f"""Давай перейдомо до оплати завдатка в 300грн та вибора способа доставки.
Тицяй ось тут і оплати легко і швидко - {offer_url}"""
    )

    await state.clear()

    
    async with await connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
        async with await db_connector.cursor() as db_cursor:
            await db_cursor.execute(
                """
                INSERT INTO orders(order_id, pil_size, pil_count, status)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    pil_id,
                    pil_size,
                    pil_count,
                    "not confirmed"
                )
            )
        await db_connector.commit()


@order_pil_handler_router.message(CommandStart(deep_link=True))
async def paid_order(message: types.Message, state: FSMContext, command: CommandObject) -> None:
    """
    Start bot, send welcome message

    Command: /start
    """
    pil_id = command.args

    if "paid_order_" in pil_id:
        await create_log(message, "User paid order")

        pil_id = pil_id.replace("paid_order_", "")

        async with await connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
            async with await db_connector.cursor() as db_cursor:
                await db_cursor.execute(
                    """
                    UPDATE orders SET status=%s
                    WHERE order_id=%s
                    """,
                    (
                        "confirmed",
                        int(pil_id)
                    )
                )
            await db_connector.commit()

        await message.answer(
            f"""Дякую за оплату. 
Ви оплатили замовлення номер - {pil_id.zfill(8)}"""
        )