COOKIES = "cook.json"   #Temp file cooks for request 

#URL and HEADER for requests to faceit
URL_MAIN_FACEIT = "https://www.faceit.com/ru"
HEADERS_FACEIT = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.faceit.com/ru',
            'Origin': 'https://www.faceit.com'
        }


TOKEN_TELEGRAM_BOT = "Your TOKEN TG" #Token received from the bot @BotFather
TOKEN_FACEIT = "Your TOKEN FACEIT" #Token received from the https://docs.faceit.com

#Text for bot message
START_MESSAGE = """Для работы с ботом вы можете воспользоваться следующими командами

/watchdemo - получить демку матча
/check **id match** - получить информацию лобби этого матча
/seeker **nickname** - получать информацию лобби о новых матчах игрока
"""
#Scopes for work with Google Drive Disk
SCOPES_GD = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]
#client_secret.json - file with token for API Google Drive
CLIENT_AUTH_GD = 'client_secret.json'