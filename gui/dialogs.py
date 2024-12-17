import asyncio
import threading
import flet as ft
from gui.validators import validate_server, validate_login, validate_password


def create_settings_dialog(page: ft.Page, auth_manager, on_save_callback):
    server_field = ft.TextField(
        label="сервер",
        value=auth_manager.server,
        hint_text="http://server или https://server",
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE_400,
        width=300,
        on_change=validate_server
    )
    login_field = ft.TextField(
        label="логин",
        value=auth_manager.login,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE_400,
        width=300,
        on_change=validate_login
    )
    password_field = ft.TextField(
        label="пароль",
        value=auth_manager.password,
        password=True,
        can_reveal_password=True,
        border_color=ft.colors.GREY_300,
        focused_border_color=ft.colors.BLUE_400,
        width=300,
        on_change=validate_password
    )
    error_text = ft.Text(
        "",
        color=ft.colors.RED_400,
        size=14,
        text_align=ft.TextAlign.CENTER
    )
    progress = ft.ProgressBar(visible=False)

    async def async_save():
        progress.visible = True
        page.update()

        try:
            is_valid = await auth_manager.test_credentials(
                login_field.value,
                password_field.value,
                server_field.value
            )

            if is_valid:
                auth_manager.write_credentials(
                    login_field.value,
                    password_field.value,
                    server_field.value
                )
                dialog.open = False
                page.update()
                if on_save_callback:
                    on_save_callback(None)
            else:
                error_text.value = "Ошибка проверки данных"
                page.update()
        except Exception:
            error_text.value = "Ошибка сохранения"
            page.update()
        finally:
            progress.visible = False
            page.update()

    def save_credentials(_):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(async_save())
        finally:
            loop.close()

        threading.Thread(target=save_credentials).start()

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Настройки"),
        content=ft.Column(
            controls=[
                ft.Container(
                    content=server_field,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=login_field,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=password_field,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=error_text,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=progress,
                    alignment=ft.alignment.center
                ),
                ft.Container(height=7),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.TextButton(
                                "Сохранить",
                                on_click=save_credentials,
                                width=100
                            ),
                            ft.TextButton(
                                "Отмена",
                                on_click=lambda _: (
                                    setattr(dialog, "open", False),
                                    page.update()
                                ),
                                width=100
                            )
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    alignment=ft.alignment.center
                )
            ],
            spacing=10,
            width=400,
            height=500
        )
    )

    def open_dialog(_):
        error_text.value = ""
        progress.visible = False
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    return open_dialog


def show_snack_bar(page: ft.Page, success: bool):
    snack = ft.SnackBar(
        content=ft.Text(
            "Успешно" if success else "Ошибка записи"
        ),
        bgcolor=ft.colors.GREEN_400 if success else ft.colors.RED_400,
        duration=3000
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()
