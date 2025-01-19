import logging
from PIL import Image
import asyncio
import io
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bg_remove import bg_remove
from bg_remove.funcs.thumbnail import thumbnail
from mysql.connector.aio import connect
import mysql.connector
import config
from bot.functions.create_log import create_log
from bot.functions.get_work_time import get_work_time
from bot.functions.select_contact import select_contact

logging.basicConfig(level=logging.INFO)

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
    
    # Initialize empty image list in state
    await state.update_data(images=[])
    
    await message.answer(
        """🔽 Завантажте зображення для друку на подушці.
        
Ви можете завантажити декілька зображень.
Якість буде краща, якщо скористатися функцією завантажити, як "Файл" """
    )

    await state.set_state(CreatePillowStates.waiting_for_images)

@create_pil_handler_router.message(F.content_type.in_(['photo', 'document', 'sticker']), CreatePillowStates.waiting_for_images)
async def handle_image(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    images = state_data.get('images', [])
    
    pillow_image_io = io.BytesIO()
    
    # Save image to buffer
    if message.content_type == 'photo':
        await message.bot.download(message.photo[-1], destination=pillow_image_io)
        image_format = "png"
    elif message.content_type == 'document':
        await message.bot.download(message.document, destination=pillow_image_io)
        image_format = message.document.file_name.split(".")[-1]
    elif message.content_type == 'sticker':
        await message.bot.download(message.sticker, destination=pillow_image_io)
        image_format = "webp"
    
    if image_format not in ["png", "jpg", "jpeg", "webp", "heic"]:
        await message.answer("❌ Будь ласка, завантажте файл у форматі JPG, PNG або JPEG")
        return
    
    images.append(pillow_image_io)
    await state.update_data(images=images)
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='➕ Додати ще фото', callback_data='add_more_images')],
            [types.InlineKeyboardButton(text='✅ Завершити і обробити', callback_data='process_images')]
        ]
    )
    
    await message.answer(
        f"✨ Завантажено {len(images)} фото. Бажаєте додати ще?",
        reply_markup=keyboard
    )

@create_pil_handler_router.callback_query(F.data == 'process_images')
async def process_images(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    images = state_data.get('images', [])
    
    processing_message = await callback.message.answer(
        f"⏳ Обробляємо {len(images)} зображень..."
    )
    
    try:
        # Create a semaphore to limit concurrent processing
        sem = asyncio.Semaphore(3)  # Limit to 3 concurrent operations
        
        async def process_with_semaphore(image_io, idx):
            async with sem:
                return await create_pil_operation(image_io, callback.message, state, idx + 1)
        
        # Process all images concurrently with semaphore
        tasks = [
            process_with_semaphore(image_io, idx)
            for idx, image_io in enumerate(images)
        ]
        
        # Use asyncio.gather to run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out any failed results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        
        if successful_results:
            # Send back processed images
            for result in successful_results:
                await send_processed_image(callback.message, result)
        else:
            await callback.message.answer("❌ Виникла помилка при обробці зображень. Спробуйте ще раз.")
            
    except Exception as e:
        logging.error(f"Error processing images: {e}")
        await callback.message.answer("❌ Виникла помилка при обробці зображень. Спробуйте ще раз.")
    finally:
        await processing_message.delete()
        
async def create_pil_operation(image_io, message: types.Message, state: FSMContext, idx: int):
    """
    Handle user image and return image without background

    Handle: image or document
    """
    await create_log(message, f"create pil operation {idx}")

    contact_id = message.chat.id
    
    got_img = Image.open(image_io)
    logging.info("Opened image")

    await process_image_in_chunks(got_img, (300, 300))
    logging.info("Processed image in chunks")

    got_img_path = f"data/got_img/{contact_id}_{idx}.png"
    await asyncio.to_thread(got_img.save, got_img_path)
    logging.info(f"Saved got_img to {got_img_path}")

    await create_log(message, "got img saved")

    # Call bg_remove with the full URL
    result = await bg_remove(got_img, f"http://3059103.as563747.web.hosting-test.net/{got_img_path}")

    # Create preview
    pil_effect_img = result[1][0]  # Get the pil_effect image from the result
    preview_img = await asyncio.to_thread(thumbnail, pil_effect_img, (600, 600))

    preview_img_bytes = io.BytesIO()
    await asyncio.to_thread(preview_img.save, preview_img_bytes, format='PNG')
    preview_img_bytes.seek(0)

    return preview_img_bytes
async def send_processed_image(message: types.Message, preview_img_bytes: io.BytesIO):
    await message.answer_photo(
        types.BufferedInputFile(
            preview_img_bytes.read(),
            filename="preview.png"
        )
    )

    await create_log(message, "preview photo sent")

    inline_buttons = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='✅ Так, все чудово. Продовжити замовлення', callback_data='order_pil')],
            [types.InlineKeyboardButton(text='❌ Ні, щось не подобається. Підключити підтримку', callback_data='do_not_like_pil')],
            [types.InlineKeyboardButton(text='🆕 Хочу завантажити інше фото', callback_data='create_pil')]
        ]
    )

    await message.answer(
        """🏆 Ось, що вийшло після видалення фону.

❔Чи подобається такий результат результат?

ℹ️ Чорна лінія то є відображення контуру подушки на готовій подушці їх не буде.""",
        reply_markup=inline_buttons
    )

async def process_image_in_chunks(image, chunk_size=(300, 300)):
    width, height = image.size
    for x in range(0, width, chunk_size[0]):
        for y in range(0, height, chunk_size[1]):
            box = (x, y, x + chunk_size[0], y + chunk_size[1])
            chunk = image.crop(box)
            # Process the chunk (e.g., apply thumbnail, save, etc.)
            chunk = await asyncio.to_thread(thumbnail, chunk, chunk_size)
            chunk_path = f"data/got_img/chunk_{x}_{y}.png"
            await asyncio.to_thread(chunk.save, chunk_path)
            logging.info(f"Processed and saved chunk at {chunk_path}")
            # Release memory
            del chunk

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
        async with await db_cursor.cursor() as db_cursor:
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