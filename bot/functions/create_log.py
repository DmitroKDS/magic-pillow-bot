import logging
from aiogram import types

async def create_log(message: types.Message, log_info: str) -> None:
    """
    Create log with gived message

    Function
    """
    user_id = message.from_user.id
    user_name = message.from_user.username
    logging.info(f"{log_info} | User ID and Name: {user_id}, {user_name}")