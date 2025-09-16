import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode
from aiogram.types import InputFile
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

import config
from loggingLocal import log_print
from bot import dp, bot
from main import converter, disk, faceit

@dp.message_handler(commands=['start'])
async def hand_start(message: types.Message):
    try:
        folders = disk.getAllFolders()
        search = False
        for folder in folders:
            if folder["Name"] == str(message.chat.id):
                search = True
        if not search:
            log_print("New User")
            newFolder = disk.create_folder(str(message.chat.id))
            if not disk.create_folder(str(message.chat.id)):
                log_print("Created Folder Cloud")
            else:
                log_print("ERROR handlerTG created Folder Cloud")
        await message.answer(config.START_MESSAGE)
    except Exception as e:
            log_print(f"ERROR handlerTG {e}")
            return None

@dp.message_handler(lambda m: 'testik' in m.text)
async def send_photo_with_inputfile(message: types.Message):
    photo_path = "src\\data\\matches\\1-0d9427a1-826f-4288-956e-90f1547edf92\\img\\1-0d9427a1-826f-4288-956e-90f1547edf92.png"
    photo = InputFile(photo_path)
    await bot.send_photo(message.chat.id, photo, caption="Это изображение с использованием InputFile")


@dp.message_handler(lambda m: '/watchdemo' in m.text)
async def hand_watchdemo(message: types.Message):
    try:
        folder_id = disk.search_folder(str(message.chat.id))
        files = disk.searchNewFile(folder_id)
        url_folder = disk.build_folder_url(folder_id)
        if not files:
            await message.answer(f"В вашей папке не найдены файлы формата *.zst \n\nЗагрузите демку с фейсита по <a href='{url_folder}'>ссылке</a>", parse_mode=types.ParseMode.HTML)
        else:
            searchZST = False
            for file in files:
                if file["Name"][-4:] == ".zst":
                    searchZST = True
                    await message.answer("Найдено демо "+file["Name"]+"\nНачинаем конвертацию")
                    log_print("Searched file format .zst")
                    pathZST = disk.download_file(file)
                    log_print("Downloaded file "+file["Name"])
                    pathDEM = converter.zst_to_dem(pathZST)
                    log_print("Converted file "+file["Name"][:-4])
                    dataFile = disk.upload_file(pathDEM, folder_id)[0]
                    log_print("Uploaded file "+file["Name"][:-4])
                    if disk.delete_file(file):
                        log_print("Deleted file "+file["Name"])
                    await message.answer(f"Вы можете скачать демо со своей  <a href='{url_folder}'>папки</a>\n\nИли по ссылке <a href='"+dataFile["Link"]+"'>"+file["Name"][:-4]+"</a>", parse_mode=types.ParseMode.HTML)
            if not searchZST:
                await message.answer(f"В вашей папке не найдены файлы формата *.zst \n\nЗагрузите демку с фейсита по <a href='{url_folder}'>ссылке</a>", parse_mode=types.ParseMode.HTML)
    except Exception as e:
            log_print(f"ERROR handlerTG {e}")
            return None


@dp.message_handler(lambda m: '/check' in m.text)
async def hand_check(message: types.Message):
    try:
        id_match = message.text.split("/check")[1].strip()
        data_match = faceit.Match(faceit).get(id_match)
        print(data_match)
        if data_match:
            log_print("Searched Matched")
            text_match = "Время <a href='"+faceit.build_url_match(id_match)+"'>матча</a> "+data_match["Start"]+"-"+data_match["End"]+"\n\nКарта: "+data_match["Map"]+"\nСервер: "+data_match["Location"]+"\nСчет: "+data_match['Score']
            for team in data_match["Teams"]:
                text_match += "\n"+team+": \n"
                for player in data_match["Teams"][team]:
                    text_match +="\n<a href='"+player["URL-FaceIT"]+"'>"+player["Nickname"]+"</a>"
                    text_match += "\nElo change: "+str(player['Start Elo'])+"-"+str(player["End Elo"])
                    text_match += "\nStats: "+str(player["Kill"])+" "+str(player["Death"])+" "+str(player["Assists"])
            photo_path = data_match["Image"]
            photo = InputFile(photo_path)
            log_print("Uploaded photo")
            await bot.send_photo(message.chat.id, photo)
            await bot.send_message(message.chat.id, text_match, parse_mode=types.ParseMode.HTML)
    except Exception as e:
            log_print(f"ERROR handlerTG {e}")
            return None

@dp.message_handler(lambda m: '/seeker' in m.text)
async def hand_check(message: types.Message):
    try:
        nickname_player = message.text.split("/seeker")[1].strip()
        
    except Exception as e:
            log_print(f"ERROR handlerTG {e}")
            return None
