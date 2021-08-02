from pyppeteer.page import Page
from typing import Coroutine
from pathlib import Path


async def install_mouse_helper(page: Page) -> Coroutine[None, None, None]:
    js_text = Path(__file__).parent.joinpath("../js/mouseHelper.js").read_text()
    await page.evaluateOnNewDocument(
        "() => {"
        + js_text
        + "}"  # Concat here because Pyppeteer takes this arg as an anonymous function.
    )
