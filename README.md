# Python Ghost Cursor
Python port of <a href="https://github.com/Xetera/ghost-cursor">Xetera/ghost-cursor</a>, for use with Pyppeteer and Playwright.

> Generate realistic, human-like mouse movement data between coordinates or navigate between elements with Pyppeteer/Playwright
like the definitely-not-robot you are.

## Installation
`pip install python_ghost_cursor`

## Usage

Generating movement data between 2 coordinates.

```python
from python_ghost_cursor import path

start = {
    "x": 220,
    "y": 402,
}

end = {
    "x": 902,
    "y": 1032,
}

route = path(start, end)

 # [
 #   { "x": 100, "y": 100 },
 #   { "x": 108.75573501957051, "y": 102.83608396351725 },
 #   { "x": 117.54686481838543, "y": 106.20019239793275 },
 #   { "x": 126.3749821408895, "y": 110.08364505509256 },
 #   { "x": 135.24167973152743, "y": 114.47776168684264 }
 #   ... and so on
 # ]
```

Usage with Pyppeteer:

```python
import asyncio
import pyppeteer
from python_ghost_cursor.pyppeteer import create_cursor

async def main(url):
  selector = "#sign-up button"
  browser = await pyppeteer.launch(headless=False)
  page = await browser.newPage()
  cursor = createCursor(page)
  await page.goto(url)
  await page.waitForSelector(selector)
  await cursor.click(selector)

asyncio.run(main())

```

Usage with Playwright (async):

```python
import asyncio
from playwright.async_api import async_playwright
from python_ghost_cursor.playwright.async_api import create_cursor

async def main():
  async with async_playwright() as p:
    selector = "#sign-up button"
    browser = await p.chromium.launch(channel="chrome", headless=False)
    page = await browser.new_page()
    cursor = create_cursor(page)
    await page.goto(url)
    await page.wait_for_selector(selector)
    await cursor.click(selector)

asyncio.run(main())

```

Usage with Playwright (sync):

```python
from playwright.sync_api import sync_playwright
from python_ghost_cursor.playwright.sync_api import create_cursor

def main():
  sync with sync_playwright() as p:
    selector = "#sign-up button"
    browser = p.chromium.launch(channel="chrome", headless=False)
    page = browser.new_page()
    cursor = create_cursor(page)
    page.goto(url)
    page.wait_for_selector(selector)
    cursor.click(selector)

main()

```
## More info
The original repo gives <a href="https://github.com/Xetera/ghost-cursor#puppeteer-specific-behavior"> a description of some of the cool features</a>, along with <a href="https://github.com/Xetera/ghost-cursor#how-does-it-work">a good explanation of how it works.</a>

