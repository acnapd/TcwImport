# Настройки окна
WINDOW_WIDTH = 390
WINDOW_HEIGHT = 500
WINDOW_TITLE = "Импорт температуры холодной воды источников"

# Настройки API
API_LOGIN_ENDPOINT = "/api/v1/Login"
API_NODES_ENDPOINT = "/api/v1/Core/Nodes"

# Настройки шифрования
ENCRYPTION_KEY_BASE = 'Pv2PXujA19CmIidkigTbaYxv2gZosW8cdmypsvhVDP0='

# Настройки файлов
CREDENTIALS_FILE = "credentials.txt"
ICON_PATH = "/icon-32.ico"

# Регулярные выражения для валидации
SERVER_PATTERN = (
    r'^$|^h$|^ht$|^htt$|^http$|^https$|^https?:$|^https?:/$|'
    r'^https?://$|^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]*$'
)
LOGIN_PATTERN = r'^[a-zA-Z0-9]*$'
PASSWORD_PATTERN = r'^[a-zA-Z0-9]*$'
NUMBER_PATTERN = r'^-?[0-9]{1,2}[.,]?[0-9]{0,2}$'

# Настройки кэширования
API_KEY_CACHE_TIMEOUT = 3000  # в секундах
