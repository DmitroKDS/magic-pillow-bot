from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode

from config import BOT_TOKEN_API


bot = Bot(
    token=BOT_TOKEN_API,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)