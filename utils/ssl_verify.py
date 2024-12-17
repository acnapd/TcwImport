import ssl
import certifi
import requests
from urllib.parse import urlparse


def verify_ssl_cert(url: str) -> tuple[bool, str]:
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme != 'https':
            return True, "Соединение не использует SSL"

        response = requests.get(url, verify=certifi.where())
        return True, "SSL-сертификат действителен"
    except requests.exceptions.SSLError as e:
        return False, f"Ошибка SSL: {str(e)}"
    except requests.exceptions.RequestException as e:
        return False, f"Ошибка соединения: {str(e)}"


def get_ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context(cafile=certifi.where())
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    return context
