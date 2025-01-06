from aiogram import Router, types, F

from bot.functions.create_log import create_log
from bot.functions.get_work_time import get_work_time

import os

from mysql.connector.aio import connect
import config

from bot.functions.select_contact import select_contact


examples_handler_router = Router()


@examples_handler_router.message(lambda message: message.text == '🔍 Переглянути приклади')
async def examples(message: types.Message) -> None:
    """
    Give examples of the pillows, bot send examples of pillow or user can ask a question

    Button: about pil
    """
    await create_log(message, "examples")

    await message.answer(
        """🖼 Ось кілька прикладів наших подушок:"""
    )

    media = [types.InputMediaPhoto(media=types.FSInputFile(f"data/pil_examples/{image}")) for image in os.listdir("data/pil_examples/")]

    if media:
        await message.answer_media_group(
            media
        )

    inline_buttons = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='🌟 Створити подушку', callback_data='create_pil')],
            [types.InlineKeyboardButton(text='❓ В мене є питання', callback_data='question_1')]
        ]
    )

    await message.answer(
        """❓ Сподобалися приклади?
✅ Можемо перейти до створення подушки?""",
        reply_markup=inline_buttons
    )


@examples_handler_router.callback_query(F.data.contains('question'))
async def question(callback_query: types.CallbackQuery) -> None:
    """
    Ask additional questions, bor check if can message to manager

    Button: additional questions pil
    """
    await create_log(callback_query.message, "question")

    is_work_time = get_work_time()

    contact_id = callback_query.message.chat.id
    question = {"1":'Питання до Менеджера з прикладів', "2":'Питання до Менеджера з про подушку'}[callback_query.data.split('_')[-1]]
    contact = await select_contact(contact_id)

    if is_work_time:
        await callback_query.message.answer(
            f"""🚀 Я зараз покличу нашого менеджера {contact[0]} (+{contact[1]})! Менеджер скоро зв’яжеться з вами! 📞✨"""
        )
    else:
        await callback_query.message.answer(
            f"""Наші менеджери зараз відпочивають. Ми працюємо з понеділка по п'ятницю з 9 до 18, а також у суботу з 10 до 14. Тому трішки почекайте  {contact[0]} (+{contact[1]}) і ми обов'язково відповімо, як тільки зможемо :-)"""
        )


    contact_id = callback_query.message.chat.id

    async with await connect(host=config.HOST, user=config.USER, password=config.PASSWORD, database=config.DB) as db_connector:
        async with await db_connector.cursor() as db_cursor:
            await db_cursor.execute("INSERT INTO messages(direct, message, contact_id) VALUES (%s, %s, %s)",
                (
                    'manager',
                    question,
                    contact_id
                )
            )
        await db_connector.commit()