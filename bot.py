from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import config
from loggingLocal import log_print

bot = Bot(config.TOKEN_TELEGRAM_BOT)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)