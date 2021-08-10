from pyppeteer.page import Page
from pathlib import Path


async def install_mouse_helper(page: Page):
    js_text = Path(__file__).parent.joinpath("../js/mouseHelper.js").read_text()
    await page.evaluateOnNewDocument(
        "() => {"
        + js_text
        + "}"  # Concat here because Pyppeteer takes this arg as an anonymous function.
    )
