import asyncio

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot_instance import bot
from bot.main_handler import main_handler_router
from bot.exmaples_handler import examples_handler_router
from bot.create_pil_handler import create_pil_handler_router
from bot.order_pil_handler import order_pil_handler_router

from db import create_db

from bot.error_handler import error_handler

import logging

import os


def create_folders(folder_name) -> None:
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def register_routes(dispatcher: Dispatcher) -> None:
    """
    Initialize routes of the bot
    """
    logging.info(f"Initialize routers")

    dispatcher.include_router(order_pil_handler_router)
    dispatcher.include_router(main_handler_router)
    dispatcher.include_router(examples_handler_router)
    dispatcher.include_router(create_pil_handler_router)

async def main() -> None:
    """
    The main function that create and start bot
    """
    create_folders("data")
    create_folders("data/got_img")
    create_folders("data/no_bg")
    create_folders("data/pil_effect")

    await create_db()

    dispatcher = Dispatcher(storage=MemoryStorage())

    dispatcher.errors.register(error_handler)

    register_routes(dispatcher)

    logging.info(f"Bot have been runing")
    await dispatcher.start_polling(bot, timeout=160)


if __name__ == '__main__':
    # Start loggining

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("bot_logs.log"),
            logging.StreamHandler(),
        ],
    )


    # Run the bot

    logging.info(f"Run the bot")

    asyncio.run(main())