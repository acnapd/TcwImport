import asyncio
import threading
import flet as ft
from typing import List
from config.settings import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    ICON_PATH
)
from core.auth import AuthManager
from core.api import ApiManager
from gui.dialogs import create_settings_dialog, show_snack_bar
from gui.validators import validate_number
from utils.excel import export_to_excel, import_from_excel
from datetime import datetime


class TcwImportApp:
    def __init__(self):
        self.auth_manager = AuthManager()
        self.api_manager = ApiManager(self.auth_manager)
        self.sources = []
        self.labels = []
        self.page = None
        self.file_picker = None
        self.save_file_dialog = None

    def run_async(self, coro):
        if coro is None:
            return

        async def wrapper():
            try:
                await coro
            except Exception:
                pass

        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(wrapper())
            except Exception:
                pass
            finally:
                try:
                    pending = asyncio.all_tasks(loop)
                    if pending:
                        loop.run_until_complete(asyncio.gather(
                            *pending, return_exceptions=True))
                except Exception:
                    pass
                finally:
                    try:
                        loop.close()
                    except Exception:
                        pass

        threading.Thread(target=run).start()

    def handle_file_picker_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            try:
                data = import_from_excel(e.files[0].path)
                for item in data:
                    for i, label in enumerate(self.labels):
                        if item['src'] == label:
                            self.sources[i].value = str(item['tcw'])
                            self.sources[i].update()
                show_snack_bar(self.page, True)
            except Exception:
                show_snack_bar(self.page, False)

    def handle_save_result(self, e: ft.FilePickerResultEvent):
        if e.path:
            try:
                filepath = e.path if e.path.endswith(
                    '.xlsx') else f"{e.path}.xlsx"
                export_to_excel(self.export_data_buffer, filepath)
                show_snack_bar(self.page, True)
            except Exception:
                show_snack_bar(self.page, False)

    def export_data(self, _):
        try:
            data = []
            for label, source in zip(self.labels, self.sources):
                try:
                    temp = float(source.value.replace(",", ".")
                                 ) if source.value else None
                except (ValueError, AttributeError):
                    temp = None

                data.append({
                    'Источник': label,
                    'Температура': temp
                })

            if self.labels:
                self.export_data_buffer = data
                default_name = f"temperature_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                self.save_file_dialog.save_file(
                    allowed_extensions=['xlsx'],
                    file_name=default_name
                )
            else:
                show_snack_bar(self.page, False)
        except Exception:
            show_snack_bar(self.page, False)

    def initialize_window(self, page: ft.Page):
        self.page = page
        page.window.width = WINDOW_WIDTH
        page.window.height = WINDOW_HEIGHT
        page.window.resizable = False
        page.window.maximizable = False
        page.window.minimizable = True
        page.window.center()
        page.title = WINDOW_TITLE
        page.window.title = WINDOW_TITLE

        page.window.prevent_close = False
        page.window.always_on_top = False
        page.window.to_front = False
        page.window.opacity = 1.0
        page.window.skip_task_bar = False
        page.window.frameless = False
        page.window.progress_bar = None
        page.window.focused = True
        page.window.visible = True
        page.window.full_screen = False
        page.window.bgcolor = None
        page.window.transparent = False
        page.window.taskbar_icon = ICON_PATH
        page.window.icon = ICON_PATH
        page.icon = ICON_PATH

        page.padding = 5
        page.spacing = 5
        page.auto_scroll = False

        self.file_picker = ft.FilePicker(
            on_result=self.handle_file_picker_result
        )
        page.overlay.append(self.file_picker)

        self.save_file_dialog = ft.FilePicker(
            on_result=self.handle_save_result
        )
        page.overlay.append(self.save_file_dialog)

    def grab_data(self) -> List[dict]:
        data = [
            [label, source.value.replace(",", ".")]
            for label, source in zip(self.labels, self.sources)
        ]
        return [item for item in data if item[1]]

    async def push_data_with_status_async(self, _):
        progress = ft.ProgressBar()
        self.page.overlay.append(progress)
        self.page.update()

        try:
            node_attributes = await self.api_manager.filter_node_attributes(self.labels)
            if not node_attributes:
                show_snack_bar(self.page, False)
                return

            node_data = [
                dict(zip(['src', 'nodeid'], item))
                for item in node_attributes
            ]
            input_data = [
                dict(zip(['src', 'tcw'], item))
                for item in self.grab_data()
            ]

            if not node_data or not input_data:
                show_snack_bar(self.page, False)
                return

            merged_data = self.api_manager.merge_data(node_data, input_data)
            if not merged_data:
                show_snack_bar(self.page, False)
                return

            result = await self.api_manager.push_temperature_data(merged_data)
            show_snack_bar(self.page, bool(result))
        except Exception:
            show_snack_bar(self.page, False)
        finally:
            self.page.overlay.remove(progress)
            self.page.update()

    def push_data_with_status(self, e):
        self.run_async(self.push_data_with_status_async(e))

    def refresh_sources(self, _=None):
        if self.page is None:
            return
        self.run_async(self.refresh_sources_async())

    async def refresh_sources_async(self):
        if not self.page:
            return

        progress = ft.ProgressBar()
        self.page.overlay.append(progress)
        self.page.update()

        try:
            sources = await self.api_manager.get_sources_names()
            if sources is None:
                show_snack_bar(self.page, False)
                return

            self.labels = sources if sources else []
            self.sources = []

            base_height = 500
            item_height = 50
            max_height = base_height * 3

            desired_height = len(self.labels) * item_height
            window_height = min(desired_height, max_height) if len(
                self.labels) > 6 else base_height
            self.page.window.height = window_height

            content = ft.Column(
                spacing=8,
                tight=True,
                height=window_height,
                scroll=desired_height > max_height
            )

            button_row = ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.SETTINGS,
                        icon_color=ft.colors.BLUE_400,
                        tooltip="Настройки",
                        on_click=create_settings_dialog(
                            self.page,
                            self.auth_manager,
                            self.refresh_sources
                        )
                    ),
                    ft.IconButton(
                        icon=ft.icons.FILE_UPLOAD,
                        icon_color=ft.colors.BLUE_400,
                        tooltip="Импорт из Excel",
                        on_click=lambda _: self.file_picker.pick_files(
                            allowed_extensions=['xlsx']
                        )
                    ),
                    ft.IconButton(
                        icon=ft.icons.FILE_DOWNLOAD,
                        icon_color=ft.colors.BLUE_400,
                        tooltip="Экспорт в Excel",
                        on_click=self.export_data
                    ),
                    ft.Container(
                        expand=True,
                        alignment=ft.alignment.center
                    ),
                    ft.ElevatedButton(
                        "Записать значения Тхв",
                        icon=ft.icons.UPLOAD,
                        on_click=self.push_data_with_status,
                        disabled=not self.labels
                    )
                ],
                spacing=0,
                tight=True
            )

            if not self.labels:
                content.controls.append(
                    ft.Container(
                        content=ft.Text(
                            "Для работы приложения тебуется пользовательский "
                            "атрибут Объекта Учёта 'sourceName' содержащий "
                            "название источника",
                            size=14,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.colors.GREY_700,
                            weight=ft.FontWeight.NORMAL,
                            width=350
                        ),
                        alignment=ft.alignment.center,
                        padding=ft.padding.only(top=20, bottom=20)
                    )
                )
            else:
                for label in self.labels:
                    row = ft.Row(
                        controls=[
                            ft.Text(label, size=14, width=250),
                            ft.TextField(
                                width=100,
                                height=35,
                                text_align=ft.TextAlign.CENTER,
                                content_padding=ft.padding.only(
                                    left=5, right=5, top=5),
                                keyboard_type=ft.KeyboardType.NUMBER,
                                border_color=ft.colors.GREY_300,
                                focused_border_color=ft.colors.BLUE_400,
                                on_change=validate_number
                            )
                        ],
                        tight=True
                    )
                    content.controls.append(row)
                    self.sources.append(row.controls[1])

            content.controls.append(button_row)

            self.page.clean()
            self.page.add(content)
            self.page.update()
        finally:
            self.page.overlay.remove(progress)
            self.page.update()

    async def main_async(self, page: ft.Page):
        try:
            self.initialize_window(page)

            if not self.auth_manager.load_credentials():
                settings_dialog = create_settings_dialog(
                    page,
                    self.auth_manager,
                    self.refresh_sources
                )
                settings_dialog(None)
            else:
                await self.refresh_sources_async()
        except Exception:
            show_snack_bar(page, False)

    def main(self, page: ft.Page):
        try:
            self.initialize_window(page)

            if not self.auth_manager.load_credentials():
                settings_dialog = create_settings_dialog(
                    page,
                    self.auth_manager,
                    self.refresh_sources
                )
                settings_dialog(None)
            else:
                content = ft.Column(
                    spacing=8,
                    tight=True,
                    height=WINDOW_HEIGHT,
                    scroll=False
                )
                self.page.add(content)
                self.refresh_sources()

        except Exception:
            show_snack_bar(page, False)

    async def cleanup(self):
        if hasattr(self, 'auth_manager'):
            await self.auth_manager.close_session()
        if hasattr(self, 'api_manager'):
            await self.api_manager.close_session()
