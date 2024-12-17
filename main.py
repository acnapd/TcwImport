import flet as ft
from gui.app import TcwImportApp


async def main(page: ft.Page):
    app = TcwImportApp()
    try:
        await app.main(page)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await app.cleanup()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="icons")
