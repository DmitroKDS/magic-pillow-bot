from aiogram import Router, types, F

from bot.functions.create_log import create_log
from bot.functions.get_work_time import get_work_time

from aiogram.fsm.context import FSMContext
from bot.functions.bot_states import create_pil_img

import io

from bg_remove import bg_remove

from mysql.connector.aio import connect
import mysql.connector
import config

import asyncio

from bot.functions.select_contact import select_contact

from PIL import Image
from bg_remove.funcs.thumbnail import thumbnail

from aiogram.fsm.state import State, StatesGroup

class CreatePillowStates(StatesGroup):
    waiting_for_images = State()
    processing = State()

create_pil_handler_router = Router()

@create_pil_handler_router.message(lambda message: message.text == '✨ Створити подушку')
@create_pil_handler_router.callback_query(F.data == 'create_pil')
async def create_pil(message: types.Message | types.CallbackQuery, state: FSMContext) -> None:
    """
    Create pillow, bot send info about creating pillow

    Button: create pil
    """
    if isinstance(message, types.CallbackQuery):
        message = message.message

    await create_log(message, "create pil")
    
    await message.answer(
        """🔽 Завантажте зображення для друку на подушці.
        
Ви можете завантажити декілька зображень.
Якість буде краща, якщо скористатися функцією завантажити, як "Файл" """
    )

    await state.set_state(CreatePillowStates.waiting_for_images)

ALLOWED_FORMATS = {'png', 'jpg', 'jpeg', 'webp', 'heic'}

@create_pil_handler_router.message(F.content_type.in_(['photo', 'document', 'sticker']), create_pil_img.is_waiting)
async def handle_image(message: types.Message, state: FSMContext):
    """Handle incoming images and prepare them for processing"""
    async def validate_image(img_io) -> tuple[bool, str]:
        try:
            img_io.seek(0)
            with Image.open(img_io) as img:
                return True, ""
        except Exception:
            return False, "Неправильний формат файлу"

    images_to_validate = []
    
    if message.media_group_id:
        state_data = await state.get_data()
        media_key = f'media_{message.media_group_id}'
        media_dict = state_data.get(media_key, {'images': [], 'processed': False})
        
        if media_dict['processed']:
            return
            
        img_io = io.BytesIO()
        if message.content_type == 'photo':
            await message.bot.download(message.photo[-1], destination=img_io)
        elif message.content_type == 'document':
            await message.bot.download(message.document, destination=img_io)
            
        is_valid, error_msg = await validate_image(img_io)
        if not is_valid:
            await message.answer(f"⚠️ {error_msg}")
            return
            
        media_dict['images'].append(img_io)
        await state.update_data({media_key: media_dict})
        
        await asyncio.sleep(0.5)
        media_dict = (await state.get_data())[media_key]
        if len(media_dict['images']) < len(message.media_group):
            return
            
        images_to_validate = media_dict['images']
        media_dict['processed'] = True
        await state.update_data({media_key: media_dict})
    else:
        img_io = io.BytesIO()
        if message.content_type == 'photo':
            await message.bot.download(message.photo[-1], destination=img_io)
        elif message.content_type == 'document':
            await message.bot.download(message.document, destination=img_io)
        elif message.content_type == 'sticker':
            await message.bot.download(message.sticker, destination=img_io)
            
        is_valid, error_msg = await validate_image(img_io)
        if not is_valid:
            await message.answer(f"⚠️ {error_msg}")
            return
            
        images_to_validate = [img_io]

    if images_to_validate:
        image_count = len(images_to_validate)
        await state.update_data(pending_images=images_to_validate)
        
        confirm_keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="✅ Так, обробити", callback_data="process_images")],
                [types.InlineKeyboardButton(text="❌ Ні, завантажити інші", callback_data="create_pil")]
            ]
        )
        
        plural_form = "зображення" if image_count == 1 else "зображень"
        await message.answer(
            f"📸 Отримано {image_count} {plural_form}. Почати обробку?",
            reply_markup=confirm_keyboard
        )

@create_pil_handler_router.callback_query(F.data == "process_images")
async def process_images(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    images_to_process = state_data.get('pending_images', [])
    
    if not images_to_process:
        await callback.message.answer("❌ Не знайдено зображень для обробки")
        return
        
    await callback.message.answer(
        "⏳ Починаємо обробку зображень...\n"
        "🤖 Це може зайняти кілька хвилин"
    )
    
    tasks = [
        create_pil_operation(img, callback.message, state, idx + 1) 
        for idx, img in enumerate(images_to_process)
    ]
    
    try:
        results = await asyncio.gather(*tasks)
        for result in results:
            preview_img_bytes, inline_buttons = result
            await callback.message.answer_photo(
                types.BufferedInputFile(
                    preview_img_bytes.read(),
                    filename="preview.png"
                ),
                reply_markup=inline_buttons
            )
    except Exception as e:
        await callback.message.answer(
            "❌ Виникла помилка під час обробки. Спробуйте ще раз або зверніться до підтримки."
        )
        print(f"Error processing images: {e}")

# Modify create_pil_operation to return the processed image data
async def create_pil_operation(image_io, message: types.Message, state: FSMContext, idx: int):
    """
    Handle user image and return image without background

    Handle: image or document
    """
    await create_log(message, f"create pil operation {idx}")

    contact_id = message.chat.id
    pillow_image_io = image_io
    image_format = "png"
    
    if message.content_type == 'photo':
        await message.bot.download(message.photo[-1], destination=pillow_image_io)
    elif message.content_type == 'document':
        await message.bot.download(message.document, destination=pillow_image_io)
        image_format = message.document.file_name.split(".")[-1]
    elif message.content_type == 'sticker':
        await message.bot.download(message.sticker, destination=pillow_image_io)
        image_format = "webp"

    if image_format in ["png", "jpg", "jpeg", "webp", "heic"]:    
        with mysql.connector.connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
            with db_connector.cursor() as db_cursor:
                db_cursor.execute("SELECT COUNT(*) FROM requests")
                request_id = db_cursor.fetchone()[0]+1
                
                db_cursor.execute("INSERT INTO requests(contact_id, request_id) VALUES (%s, %s)",
                    (contact_id, request_id)
                )
            db_connector.commit()

        request_id_str = str(request_id).zfill(8)

        await message.answer(
            f"""Твоя заявка №{request_id_str}.

✨ Чудово! Потрібно зачекати від 1 до 5 хвилин ⏳.
Наш розумний ШІ 🤖 вже аналізує зображення 🖼️ та видаляє фон 🌟!"""
        )

        got_img = Image.open(pillow_image_io)
        
        # Fix 1: Properly await the thumbnail coroutine
        thumbnailed_img = thumbnail(got_img, (1200, 1200))
        got_img_path = f"data/got_img/{request_id}.png"
        
        # Fix 2: Save the thumbnailed image directly
        thumbnailed_img.save(got_img_path)
        await create_log(message, "got img saved")

        result = await bg_remove(thumbnailed_img, f"http://3059103.as563747.web.hosting-test.net/{got_img_path}")
        no_bg_img, no_bg_img_path = result[0]
        pil_effect_img, pil_effect_img_path = result[1]

        # Fix 3: Save images directly without asyncio.to_thread since PIL's save is synchronous
        no_bg_img.save(no_bg_img_path)
        await create_log(message, "no bg img saved")

        pil_effect_img.save(pil_effect_img_path)
        await create_log(message, "pil effect img saved")

        # Fix 4: Properly await the preview thumbnail
        preview_img = thumbnail(pil_effect_img, (600, 600))
        preview_img_bytes = io.BytesIO()
        preview_img.save(preview_img_bytes, format='PNG')
        preview_img_bytes.seek(0)

        inline_buttons = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text='✅ Так, все чудово. Продовжити замовлення', callback_data='order_pil')],
                [types.InlineKeyboardButton(text='❌ Ні, щось не подобається. Підключити підтримку', callback_data='do_not_like_pil')],
                [types.InlineKeyboardButton(text='🆕 Хочу завантажити інше фото', callback_data='create_pil')]
            ]
        )

        await create_log(message, "preview photo sent")

        # Return the processed image data instead of sending it
        return preview_img_bytes, inline_buttons
    else:
        await message.answer(
        """📂 Ой, щось пішло не так! Ви завантажили файл у форматі, який ми, на жаль, не можемо обробити. 😔

✅ Завантажте, будь ласка, файл у форматі JPG, PNG або JPEG – і все запрацює! 🎉
Якщо виникнуть питання, ми завжди поруч, щоб допомогти! 😊"""
        )


@create_pil_handler_router.callback_query(F.data == 'do_not_like_pil')
async def do_not_like_pil(callback_query: types.CallbackQuery, state: FSMContext):
    """
    In user mind pil is wrong. Bot offer a help

    Button: pil not okay
    """
    await create_log(callback_query.message, "Do not like pil")


    inline_buttons = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='На макеті подушки зайвий елемент', callback_data='miss_element')],
            [types.InlineKeyboardButton(text='Інше', callback_data='other')],
            [types.InlineKeyboardButton(text='Повернутись на шаг назад', callback_data='your_mind')]
        ]
    )

    await callback_query.message.answer(
        """🤔 Що саме вам не сподобалось? Ми зробимо все, щоб ваша подушка була ТОП! 💪✨""",
        reply_markup=inline_buttons
    )


@create_pil_handler_router.callback_query(F.data == 'miss_element')
async def miss_element(callback_query: types.CallbackQuery):
    """
    In user mind element is missing. Bot offer a help

    Button: miss element
    """
    await create_log(callback_query.message, "miss element")

    is_work_time = get_work_time()

    inline_buttons = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='Чекаю відповідь', callback_data='wait_for_answer')],
            [types.InlineKeyboardButton(text='🔄 Хочу завантажити інше фото 📸', callback_data='create_pil')]
        ]
    )

    if is_work_time:
        await callback_query.message.answer(
            """😊 Ого, на щастя не все захопив ще Штучний разум!
Я вже передаю нашому дизайнеру, щоб він подивився на ваше фото 👀. Він вирішить, чи зможе прибрати зайве. ✍️🎨""",
            reply_markup=inline_buttons
        )
    else:
        await callback_query.message.answer(
            """😊 Ого, на щастя не все захопив ще Штучний разум!
Я передам нашому дизайнеру, щоб він подивився на ваше фото 👀. Він вирішить, чи зможе прибрати зайве.
Наш дизайнер зараз відпочиває. Ми працюємо з понеділка по п'ятницю з 9 до 18, а також у суботу з 10 до 14. Відповість зразу, як буде можливість. ✍️🎨""",
            reply_markup=inline_buttons
        )


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
            

            await db_cursor.execute("INSERT INTO messages(direct, message, contact_id, pil_id) VALUES (%s, %s, %s, %s)",
                (
                    'designer',
                    'Зайві деталі на зображені',
                    contact_id,
                    pil_id
                )
            )
        await db_connector.commit()



@create_pil_handler_router.callback_query(F.data == 'other')
async def other(callback_query: types.CallbackQuery):
    """
    Choose other problem

    Button: other problem
    """
    await create_log(callback_query.message, "Other")


    contact_id = callback_query.message.chat.id
    contact = await select_contact(contact_id)
    if contact is None:
        return

    is_work_time = get_work_time()

    inline_buttons = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='Чекаю відповідь', callback_data='wait_for_answer')],
            [types.InlineKeyboardButton(text='🔄 Хочу завантажити інше фото 📸', callback_data='create_pil')]
        ]
    )

    if is_work_time:
        await callback_query.message.answer(
            f"""Я вже передаю скаргу дизайнеру {contact[0]} (+{contact[1]}), і він усе перегляне та постарається знайти рішення для вас. 😉


📩 Ми обов’язково зв’яжемось з вами, як тільки дизайнер все перевірить! 💬""",
            reply_markup=inline_buttons
        )
    else:
        await callback_query.message.answer(
            f"""Я передам скаргу дизайнеру {contact[0]} (+{contact[1]}) 🖌️, і він усе перегляне та постарається знайти рішення для вас. 😉


📅 Наш графік роботи:
Понеділок – п’ятниця: 09:00 – 18:00
Субота: 10:00 – 14:00
Неділя – заслужений відпочинок. 😊

📩 Ми обов’язково зв’яжемось з вами, як тільки дизайнер все перевірить! 💬""",
            reply_markup=inline_buttons
        )


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
            

            await db_cursor.execute("INSERT INTO messages(direct, message, contact_id, pil_id) VALUES (%s, %s, %s, %s)",
                (
                    'designer',
                    'Проблеми з зображенням',
                    contact_id,
                    pil_id
                )
            )
        await db_connector.commit()



@create_pil_handler_router.callback_query(F.data == 'your_mind')
async def your_mind(callback_query: types.CallbackQuery):
    """
    User mind

    Button: your mind
    """
    await create_log(callback_query.message, "your_mind")

    inline_buttons = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='✅ Так, усе чудово✨', callback_data='order_pil')],
            [types.InlineKeyboardButton(text='❌ Ні, щось не подобається✨', callback_data='pil_is_wrong')],
            [types.InlineKeyboardButton(text='🔄 Хочу завантажити інше фото 📸', callback_data='create_pil')]
        ]
    )

    await callback_query.message.answer(
        """Чи все подобається вам в результаті?""",
        reply_markup=inline_buttons
    )