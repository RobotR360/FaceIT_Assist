import logging, asyncio
from aiogram.utils import executor

import config
from bot import dp
import handlerTG
from loggingLocal import log_print
from converter import ZSTDecoder
from webparser import WebParser
from googleDisk import GoogleDisk
from faceit import FaceITAPI
from faceit_api import FaceIT

converter = ZSTDecoder()
faceit = FaceIT(config.TOKEN_FACEIT)
disk = GoogleDisk()

if __name__ == '__main__':
    log_print("-"*10)
    log_print("START BOT")
    log_print("-"*10)
    loop = asyncio.get_event_loop()
    #loop.create_task()
    executor.start_polling(dp, skip_updates=True)
