from playwright.sync_api import Page
from pathlib import Path


def install_mouse_helper(page: Page) -> None:
    page.add_init_script(path=Path(__file__).parent.joinpath("../js/mouseHelper.js"))
