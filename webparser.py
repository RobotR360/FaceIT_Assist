from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests, json

import time, os

import config
from loggingLocal import log_print

class WebParser:

    def __init__(self):
        self.driver = self.DriverChrome()
        self.session = requests.Session()
        self.headers = config.HEADERS_FACEIT
        self.local_cookie_file = config.COOKIES

    def get_cookies(self):
        self.driver.get(config.URL_MAIN_FACEIT)
        time.sleep(5)
        cookies = self.driver.get_cookies()
        with open(self.local_cookie_file, 'w') as f:
            json.dump(cookies, f)
        self.driver.quit()
        return cookies
        
    def get_screenshot(self, url, name, attempt=3):
        path = ""
        try:
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.NAME, "roster2")))
            time.sleep(2)
            # Добавляем визуальный индикатор курсора на страницу
            self.driver.execute_script("""
            document.querySelector("#usercentrics-root").shadowRoot.querySelector("#uc-center-container > div.sc-eBMEME.kvprDO > div > div.sc-jsJBEP.jnQAFK > div > button:nth-child(2)").click()
            """)
            time.sleep(1)
            # Делаем скриншот
            os.makedirs(f"src\\data\\matches\\{name}\\img", exist_ok=True)
            self.driver.save_screenshot(f"src\\data\\matches\\{name}\\img\\{name}.png")
            path = f"src\\data\\matches\\{name}\\img\\{name}.png"
        except Exception as e:
                if attempt>0:
                    self.get_screenshot(url, name, attempt-1)
                log_print(f"ERROR webparser {e}")
                return None
        finally:
            self.driver.quit()
            return path


    def load_cookies(self):
        try:
            with open(self.local_cookie_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def attach_cookies_to_session(self, cookies):
        self.session.cookies.clear()
        for cookie in cookies:
            self.session.cookies.set(
                cookie['name'],
                cookie['value'],
                domain=cookie.get('domain'),
                path=cookie.get('path', '/')
            )

    def DriverChrome(self):
        chrome_options = Options()
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--headless")  # Раскомментируйте для безголового режима
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1000,1000")


        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def RequestGet(self, url, max_retries=3):
        for attempt in range(max_retries):
            cookies = self.load_cookies()
            if not cookies:
                cookies = self.get_cookies()
            self.attach_cookies_to_session(cookies)
            response = self.session.get(url, headers=self.headers)
            if response.status_code == 403 or "Wait..." in response.text:
                cookies = self.get_cookies_selenium()
                continue
            return response
        return response