import re
from config.settings import (
    SERVER_PATTERN,
    LOGIN_PATTERN,
    PASSWORD_PATTERN,
    NUMBER_PATTERN
)


def validate_server(event):
    if not re.match(SERVER_PATTERN, event.control.value):
        event.control.value = event.control.value[:-1]
        event.control.update()


def validate_login(event):
    if not re.match(LOGIN_PATTERN, event.control.value):
        event.control.value = event.control.value[:-1]
        event.control.update()


def validate_password(event):
    if not re.match(PASSWORD_PATTERN, event.control.value):
        event.control.value = event.control.value[:-1]
        event.control.update()


def validate_number(event):
    if event.control.value == "" or event.control.value == "-":
        return

    if not re.match(NUMBER_PATTERN, event.control.value):
        event.control.value = event.control.value[:-1]
        event.control.update()
    else:
        try:
            num = float(event.control.value.replace(",", "."))
            if num < -99.99 or num > 99.99:
                event.control.value = event.control.value[:-1]
                event.control.update()
        except ValueError:
            pass
