import httplib2
import os, io
from datetime import datetime, timezone

from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from apiclient.http import MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import config
from loggingLocal import log_print

"""Класс для работы с гугл апи"""
class GoogleDisk:
    #Инициализация класса, создание дополнительных параметров для работы с апи
    def __init__(self):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('drive', 'v3', http=http)
        self.folders = []
    
    #Получение всех директорий из корневой директории диска
    def getAllFolders(self):
        try:
            query = f"'root' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service.files().list(
                q=query,
                pageSize=10,
                fields="nextPageToken, files(id, name, createdTime)"
            ).execute()
            items = results.get('files', [])
            if not items:
                return None
            else:
                folders = []
                for item in items:
                    folders.append({"Name":item['name'], "ID":item['id'], "Time":item["createdTime"], "Link":f"https://drive.google.com/drive/folders/{item['id']}?usp=sharing"})
                return folders
        except Exception as e:
            log_print(f"ERROR googleDisk {e}")
            return None
    #Получение дополнительных параметров из локального файла или путем запроса и создания локальных файлов
    def get_credentials(self):
        try:
            home_dir = os.path.expanduser('~')
            credential_dir = os.path.join(home_dir, '.credentials')
            if not os.path.exists(credential_dir):
                os.makedirs(credential_dir)
            credential_path = os.path.join(credential_dir,
                                           'drive-python-quickstart.json')
            store = Storage(credential_path)
            credentials = store.get()
            if not credentials or credentials.invalid:
                flow = client.flow_from_clientsecrets(config.CLIENT_AUTH_GD, config.SCOPES_GD)
                flow.user_agent = "FaceIT Assist"
                credentials = tools.run_flow(flow, store)
            return credentials
        except Exception as e:
            log_print(f"ERROR googleDisk {e}")
            return None
    #Поиск новых файлов в определенной директории
    def searchNewFile(self, folder_id):
        try:
            query = f"'{folder_id}' in parents and trashed = false"
            results = self.service.files().list(
                q=query,
                pageSize=10,
                fields="nextPageToken, files(id, name, createdTime, mimeType)"
            ).execute()
            items = results.get('files', [])
            if not items:
                return None
            else:
                files = []
                for item in items:
                    files.append({"Name":item['name'], "ID":item['id'], "Time":item["createdTime"], "Type":item['mimeType']})
                return files
        except Exception as e:
            log_print(f"ERROR googleDisk {e}")
            return None
    #Скачивание определенного файла
    def download_file(self, dataFile):
        try:
            if dataFile["Name"] is None:
                file_metadata = self.service.files().get(fileId=dataFile["ID"]).execute()
                file_name = file_metadata['name']
            file_path = os.path.join("downloads\\", dataFile["Name"])
            if not os.path.exists(file_path):
                request = self.service.files().get_media(fileId=dataFile["ID"])
                fh = io.FileIO(file_path, 'wb')
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
            return file_path
        except Exception as e:
            log_print(f"ERROR googleDisk {e}")
            return None
    #Расчет сколько времени файл лежит в облаке
    def calculate_age(self, createdTime):
        file_time = datetime.fromisoformat(createdTime.replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)
        print(current_time)
        time_difference = current_time - file_time
        total_seconds = abs(time_difference.total_seconds())
        hours = total_seconds // 3600
        return hours
    #Выгрузка файла в облако с выдачей прав доступа по ссылке
    def upload_file(self, file_path, folder_id):
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File {file_path} not found")

            file_name = file_path[10:]
            file_metadata = {"name": file_name, "parents":[folder_id]}
            media = MediaFileUpload(file_path, mimetype="application/octet-stream")
            file = (
                self.service.files()
                .create(body=file_metadata, media_body=media, fields="id, webContentLink")
                .execute()
            )
            file = [{"ID":file.get('id'), "Link":file.get('webContentLink')}]
            permission = {
                'type': 'anyone',
                'role': 'reader',
            }
            permissionsAdd = self.service.permissions().create(
                fileId=file[0]['ID'],
                body=permission,
                fields='id'
            ).execute()
            return file
        except Exception as e:
            
            return None
    #Создание новой директории с выдачей прав доступа по ссылке
    def create_folder(self, folder_name):
        try:
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false and 'root' in parents"
            results = self.service.files().list(q=query, fields="files(id)").execute()
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            file_metadata['parents'] = ["root"]
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            permission = {
                'type': 'anyone',
                'role': 'writer',
            }
            permissionsAdd = self.service.permissions().create(
                fileId=folder.get('id'),
                body=permission,
                fields='id'
            ).execute()
            return folder.get('id')
        except Exception as e:
            log_print(f"ERROR googleDisk {e}")
            return None
    #Сборка ссылки
    def build_folder_url(self, folder_id):
        return f"https://drive.google.com/drive/folders/{folder_id}?usp=sharing"
    #Получение айди директории по ее названию
    def search_folder(self, name):
        try:
            query = f"'root' in parents and trashed = false and mimeType = 'application/vnd.google-apps.folder'"
            results = self.service.files().list(
                q=query,
                pageSize=10,
                fields="nextPageToken, files(id, name, createdTime, mimeType)"
            ).execute()
            items = results.get('files', [])
            if not items:
                return None
            else:
                for item in items:
                    if item['name'] == name:
                        #folders.append({"Name":item['name'], "ID":item['id'], "Time":item["createdTime"], "Type":item['mimeType']})
                        return item["id"]
        except Exception as e:
            log_print(f"ERROR googleDisk {e}")
            return None
    #Безвозвратное удаление файла из облака
    def delete_file(self, file):
        try:
            self.service.files().delete(fileId=file["ID"]).execute()
            return True
        except Exception as e:
            log_print(f"ERROR googleDisk {e}")
            return None
