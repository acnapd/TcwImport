import time
import json
import aiohttp
from typing import Optional
from config.settings import (
    API_LOGIN_ENDPOINT,
    CREDENTIALS_FILE,
    API_KEY_CACHE_TIMEOUT
)
from core.encryption import encrypt_data, decrypt_data


class AuthManager:
    def __init__(self):
        self.login = ""
        self.password = ""
        self.server = ""
        self.api_key_cache = {"key": None, "timestamp": 0}
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Контекстный менеджер для сессии"""
        await self.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие сессии при выходе из контекста"""
        await self.close_session()

    async def get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии"""
        try:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(force_close=True))
            return self._session
        except Exception:
            raise

    async def close_session(self):
        """Закрытие сессии"""
        try:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
        except Exception:
            raise

    def write_credentials(self, login: str, password: str, server: str):
        """Сохранение учетных данных"""
        self.login = login
        self.password = password
        self.server = server
        data = json.dumps({
            "login": login,
            "password": password,
            "server": server
        })
        encrypted_data = encrypt_data(data)
        with open(CREDENTIALS_FILE, "w+") as txt_file:
            txt_file.write(encrypted_data)

    def load_credentials(self) -> bool:
        """Загрузка учетных данных"""
        try:
            # Читаем файл
            with open(CREDENTIALS_FILE, "r") as file:
                encrypted_data = file.read().strip()

                # Расшифровываем и загружаем данные
                decrypted_data = decrypt_data(encrypted_data)
                credentials = json.loads(decrypted_data)

                # Загружаем данные
                self.login = credentials["login"]
                self.password = credentials["password"]
                self.server = credentials["server"]

                return True
        except FileNotFoundError:
            return False
        except json.JSONDecodeError:
            return False
        except Exception:
            return False

    async def test_credentials(self, login: str, password: str, server: str) -> bool:
        """Проверка учетных данных"""
        async with self:  # Используем контекстный менеджер
            url = f"{server}{API_LOGIN_ENDPOINT}"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            data = {
                "login": login,
                "password": password,
                "code": "",
                "application": ""
            }

            try:
                session = await self.get_session()
                async with session.post(url, headers=headers, json=data) as response:
                    response.raise_for_status()
                    return True
            except Exception:
                return False

    async def get_api_key(self) -> str:
        """Получение API ключа с кэшированием"""
        async with self:  # Используем контекстный менеджер
            current_time = time.time()
            if (self.api_key_cache["key"] is not None and
                    current_time - self.api_key_cache["timestamp"] < API_KEY_CACHE_TIMEOUT):
                return self.api_key_cache["key"]

            url = f"{self.server}{API_LOGIN_ENDPOINT}"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            data = {
                "login": self.login,
                "password": self.password,
                "code": "",
                "application": ""
            }

            try:
                session = await self.get_session()
                async with session.post(url, headers=headers, json=data) as response:
                    response.raise_for_status()
                    result = await response.json()
                    token = result["token"]
                    self.api_key_cache["key"] = token
                    self.api_key_cache["timestamp"] = current_time
                    return token
            except Exception:
                return False
