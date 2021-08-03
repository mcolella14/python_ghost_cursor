from playwright.async_api import Page
from typing import Coroutine
from pathlib import Path


async def install_mouse_helper(page: Page) -> Coroutine[None, None, None]:
    await page.add_init_script(
        path=Path(__file__).parent.joinpath("../js/mouseHelper.js")
    )