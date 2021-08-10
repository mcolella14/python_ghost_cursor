import asyncio
import logging
import random
from typing import Union, Coroutine, Optional, Dict, List
from pyppeteer.page import Page

try:
    # pyppeteer/pyppeteer@pup2.1.1 branch
    # https://github.com/pyppeteer/pyppeteer/blob/pup2.1.1/pyppeteer/jshandle.py
    from pyppeteer.jshandle import ElementHandle
except ModuleNotFoundError:
    # pyppeteer/pyppeteer@dev branch
    # https://github.com/pyppeteer/pyppeteer/blob/dev/pyppeteer/element_handle.py
    from pyppeteer.element_handle import ElementHandle

from python_ghost_cursor.shared._math import (
    Vector,
    origin,
    overshoot,
)
from python_ghost_cursor.shared._spoof import (
    path,
    should_overshoot,
    get_random_box_point,
)


logger = logging.getLogger(__name__)


async def get_random_page_point(page: Page) -> Coroutine[None, None, Vector]:
    """Get a random point on a browser window"""
    target_id = page.target._targetId
    window = await page._client.send(
        "Browser.getWindowForTarget", {"targetId": target_id}
    )
    return get_random_box_point(
        {
            "x": origin.x,
            "y": origin.y,
            "width": window["bounds"]["width"],
            "height": window["bounds"]["height"],
        }
    )


async def get_element_box(
    page: Page, element: ElementHandle, relative_to_main_frame: bool = True
) -> Coroutine[None, None, Optional[Dict[str, float]]]:
    """Using this method to get correct position of Inline elements (elements like <a>)"""
    if "objectId" not in element._remoteObject:
        return None
    quads = None
    try:
        quads = await page._client.send(
            "DOM.getContentQuads",
            {
                "objectId": element._remoteObject["objectId"],
            },
        )
    except:
        logger.debug("Quads not found, trying regular bounding_box")
        return await element.boundingBox()
    element_box = {
        "x": quads["quads"][0][0],
        "y": quads["quads"][0][1],
        "width": quads["quads"][0][4] - quads["quads"][0][0],
        "height": quads["quads"][0][5] - quads["quads"][0][1],
    }
    if element_box is None:
        return None
    if not relative_to_main_frame:
        element_frame = element.executionContext.frame
        parent_frame = await element_frame.parent_frame
        frame = None
        if parent_frame:
            iframes = parent_frame.xpath("//iframe")
            for iframe in iframes:
                if (await iframe.contentFrame()) == element_frame:
                    frame = iframe
        if frame is not None:
            bounding_box = await frame.boundingBox()
            element_box.x = (
                element_box.x - bounding_box.x
                if bounding_box is not None
                else element_box.x
            )
            element_box.y = (
                element_box.y - bounding_box.y
                if bounding_box is not None
                else element_box.y
            )
    return element_box


class GhostCursor:
    def __init__(self, page: Page, start: Vector):
        self.page = page
        self.previous = start
        self.moving = False
        self.overshoot_spread = 10
        self.overshoot_radius = 120

    async def random_move(self):
        """Start random mouse movements. Function recursively calls itself"""
        try:
            if not self.moving:
                rand = await get_random_page_point(self.page)
                await self.trace_path(path(self.previous, rand), True)
                self.previous = rand
            await asyncio.sleep(random.random() * 2)
            asyncio.ensure_future(
                self.random_move()
            )  # fire and forget, recursive function
        except:
            logger.debug("Warning: stopping random mouse movements")

    async def trace_path(self, vectors: List[Vector], abort_on_move: bool = False):
        """Move the mouse over a number of vectors"""
        for v in vectors:
            try:
                # In case this is called from random mouse movements and the users wants to move the mouse, abort
                if abort_on_move and self.moving:
                    return
                await self.page.mouse.move(v.x, v.y)
                self.previous = v
            except Exception as exc:
                # Exit function if the browser is no longer connected
                if not self.page.browser.isConnected:
                    return
                logger.debug("Warning: could not move mouse, error message: %s", exc)

    def toggle_random_move(self, random_: bool) -> None:
        self.moving = not random_

    async def click(
        self,
        selector: Optional[Union[str, ElementHandle]],
        padding_percentage: Optional[float] = None,
        wait_for_selector: Optional[float] = None,
        wait_for_click: Optional[float] = None,
    ):
        self.toggle_random_move(False)
        if selector is not None:
            await self.move(selector, padding_percentage, wait_for_selector)
            self.toggle_random_move(False)

        try:
            await self.page.mouse.down()
            if wait_for_click is not None:
                await asyncio.sleep(wait_for_click / 1000)
            await self.page.mouse.up()
        except Exception as exc:
            logger.debug("Warning: could not click mouse, error message: %s", exc)

        await asyncio.sleep(random.random() * 2)
        self.toggle_random_move(True)

    async def move(
        self,
        selector: Union[str, ElementHandle],
        padding_percentage: Optional[float] = None,
        wait_for_selector: Optional[float] = None,
    ):
        self.toggle_random_move(False)
        elem = None
        if isinstance(selector, str):
            if "//" in selector:
                if wait_for_selector:
                    await self.page.waitForXpath(selector, timeout=wait_for_selector)
                elem = (await self.page.xpath(selector))[0]
            else:
                if wait_for_selector:
                    await self.page.waitForSelector(selector, timeout=wait_for_selector)
                elem = await self.page.querySelector(selector)
            if elem is None:
                raise Exception(
                    'Could not find element with selector "${}", make sure you\'re waiting for the elements with "puppeteer.waitForSelector"'.format(
                        selector
                    )
                )
        else:  # ElementHandle
            elem = selector

        # Make sure the object is in view
        if hasattr(elem, "_remoteObject") and "objectId" in elem._remoteObject:
            try:
                await self.page._client.send(
                    "DOM.scrollIntoViewIfNeeded",
                    {"objectId": elem._remoteObject["objectId"]},
                )
            except:
                await self.page.evaluate(
                    "e => e.scrollIntoView()", elem
                )  # use regular JS scroll method as a fallback (use Page.evaluate for backwards compatibility)
        box = await get_element_box(self.page, elem)
        if box is None:
            raise Exception(
                "Could not find the dimensions of the element you're clicking on, this might be a bug?"
            )
        destination = get_random_box_point(box, padding_percentage)
        dimensions = {"height": box["height"], "width": box["width"]}
        overshooting = should_overshoot(self.previous, destination)
        to = (
            overshoot(destination, self.overshoot_radius)
            if overshooting
            else destination
        )
        await self.trace_path(path(self.previous, to))

        if overshooting:
            bounding_box = {
                "height": dimensions["height"],
                "width": dimensions["width"],
                "x": destination.x,
                "y": destination.y,
            }
            correction = path(to, bounding_box, self.overshoot_spread)
            await self.trace_path(correction)
        self.previous = destination
        self.toggle_random_move(True)

    async def moveTo(self, destination: dict):
        destination_vector = Vector(destination["x"], destination["y"])
        self.toggle_random_move(False)
        await self.trace_path(path(self.previous, destination_vector))
        self.toggle_random_move(True)


def create_cursor(
    page, start: Union[Vector, Dict] = origin, perform_random_moves: bool = False
) -> GhostCursor:
    if isinstance(start, dict):
        start = Vector(**start)
    cursor = GhostCursor(page, start)
    if perform_random_moves:
        # Start random mouse movements. Do not await the promise but return immediately
        asyncio.ensure_future(cursor.random_move())  # fire and forget
    return cursor
