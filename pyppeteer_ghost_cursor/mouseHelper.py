from pyppeteer.page import Page
from typing import Coroutine
from pathlib import Path


async def installMouseHelper(page: Page) -> Coroutine[None, None, None]:
    await page.evaluateOnNewDocument(
        Path(__file__).parent.joinpath("js/mouseHelper.js").read_text()
    )
