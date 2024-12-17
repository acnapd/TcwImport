import base64
import subprocess
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_machine_id() -> str:
    try:
        serial = subprocess.check_output(
            'wmic bios get serialnumber').decode("utf-8")
        serial = (
            serial.replace('\n', '')
            .replace('\r', '')
            .replace('SerialNumber', '')
            .replace(' ', '')
        )
        if not serial:
            return "fallback_id"
        return serial
    except Exception:
        return "fallback_id"


def get_encryption_key() -> Fernet:
    try:
        salt = b'TcwImport_salt_123'
        machine_id = get_machine_id()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
        return Fernet(key)
    except Exception:
        raise


def encrypt_data(data: str) -> str:
    try:
        if not data:
            raise ValueError("Empty data for encryption")
        fernet = get_encryption_key()
        encrypted = fernet.encrypt(data.encode())
        return encrypted.decode()
    except Exception:
        raise ValueError("Ошибка шифрования данных")


def decrypt_data(encrypted_data: str) -> str:
    try:
        if not encrypted_data:
            raise ValueError("Empty data for decryption")
        fernet = get_encryption_key()
        decrypted = fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except Exception:
        raise ValueError("Ошибка расшифровки данных")
