# TODO:
# - Add click and moveTo
# - Double check for completion
# - Actually make a repo
# - Publish

import asyncio
import logging
import math
import numpy as np
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

from pyppeteer_ghost_cursor.math import (
    Vector,
    magnitude,
    direction,
    origin,
    bezierCurve,
    overshoot,
)


logger = logging.getLogger(__name__)


def fitts(distance: float, width: float) -> float:
    a = 0
    b = 2
    id_ = math.log2(distance / width + 1)
    return a + b * id_


def getRandomBoxPoint(box: Dict, paddingPercentage: Optional[float] = None) -> Vector:
    """Get a random point on a box"""
    paddingWidth = paddingHeight = 0
    if (
        paddingPercentage is not None
        and paddingPercentage > 0
        and paddingPercentage < 100
    ):
        paddingWidth = box["width"] * paddingPercentage / 100
        paddingHeight = box["height"] * paddingPercentage / 100
    return Vector(
        box["x"] + (paddingWidth / 2) + random.random() * (box["width"] - paddingWidth),
        box["y"]
        + (paddingHeight / 2)
        + random.random() * (box["height"] - paddingHeight),
    )


async def getRandomPagePoint(page: Page) -> Coroutine[None, None, Vector]:
    """Get a random point on a browser window"""
    targetId = page.target._targetId
    window = await page._client.send(
        "Browser.getWindowForTarget", {"targetId": targetId}
    )
    return getRandomBoxPoint(
        {
            "x": origin.x,
            "y": origin.y,
            "width": window["bounds"]["width"],
            "height": window["bounds"]["height"],
        }
    )


async def getElementBox(
    page: Page, element: ElementHandle, relativeToMainFrame: bool = True
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
        logger.debug("Quads not found, trying regular boundingBox")
        return await element.boundingBox()
    elementBox = {
        "x": quads["quads"][0][0],
        "y": quads["quads"][0][1],
        "width": quads["quads"][0][4] - quads["quads"][0][0],
        "height": quads["quads"][0][5] - quads["quads"][0][1],
    }
    if elementBox is None:
        return None
    if not relativeToMainFrame:
        elementFrame = element.executionContext.frame
        parentFrame = await elementFrame.parentFrame
        frame = None
        if parentFrame:
            iframes = parentFrame.xpath("//iframe")
            for iframe in iframes:
                if (await iframe.contentFrame()) == elementFrame:
                    frame = iframe
        if frame is not None:
            boundingBox = await frame.boundingBox()
            elementBox.x = (
                elementBox.x - boundingBox.x
                if boundingBox is not None
                else elementBox.x
            )
            elementBox.y = (
                elementBox.y - boundingBox.y
                if boundingBox is not None
                else elementBox.y
            )
    return elementBox


def path(
    start: Vector, end: Union[Dict, Vector], spreadOverride: Optional[float] = None
) -> List[Vector]:
    defaultWidth = 100
    minSteps = 25
    if isinstance(end, dict):
        width = end["width"]
        end = Vector(end["x"], end["y"])
    else:
        width = defaultWidth
    curve = bezierCurve(start, end, spreadOverride)
    length = curve.length * 0.8
    baseTime = random.random() * minSteps
    steps = math.ceil((math.log2(fitts(length, width) + 1) + baseTime) * 3)
    s_vals = np.linspace(0.0, 1.0, steps)
    points = curve.evaluate_multi(s_vals)
    vectors = []
    for i in range(steps):
        vectors.append(Vector(points[0][i], points[1][i]))
    return clampPositive(vectors)


def clampPositive(vectors: List[Vector]) -> List[Vector]:
    clamp0 = lambda elem: max(0, elem)
    return [Vector(clamp0(el.x), clamp0(el.y)) for el in vectors]


overshootThreshold = 500


def shouldOvershoot(a: Vector, b: Vector) -> bool:
    return magnitude(direction(a, b)) > overshootThreshold


class GhostCursor:
    def __init__(self, page, start: Vector):
        self.page = page
        self.previous = start
        self.moving = False
        self.overshootSpread = 10
        self.overshootRadius = 120

    async def randomMove(self) -> Coroutine[None, None, None]:
        """Start random mouse movements. Function recursively calls itself"""
        try:
            if not self.moving:
                rand = await getRandomPagePoint(self.page)
                await self.tracePath(path(self.previous, rand), True)
                self.previous = rand
            await asyncio.sleep(random.random() * 2)
            asyncio.ensure_future(
                self.randomMove()
            )  # fire and forget, recursive function
        except:
            logger.debug("Warning: stopping random mouse movements")

    async def tracePath(
        self, vectors: List[Vector], abortOnMove: bool = False
    ) -> Coroutine[None, None, None]:
        """Move the mouse over a number of vectors"""
        for v in vectors:
            try:
                # In case this is called from random mouse movements and the users wants to move the mouse, abort
                if abortOnMove and self.moving:
                    return
                await self.page.mouse.move(v.x, v.y)
                self.previous = v
            except Exception as exc:
                # Exit function if the browser is no longer connected
                if not self.page.browser.isConnected:
                    return
                logger.debug("Warning: could not move mouse, error message: %s", exc)

    def toggleRandomMove(self, random_: bool):
        self.moving = not random_

    async def click(
        self,
        selector: Optional[Union[str, ElementHandle]],
        paddingPercentage: Optional[float] = None,
        waitForSelector: Optional[float] = None,
        waitForClick: Optional[float] = None,
    ):
        self.toggleRandomMove(False)
        if selector is not None:
            await self.move(selector, paddingPercentage, waitForSelector)
            self.toggleRandomMove(False)

        try:
            await self.page.mouse.down()
            if waitForClick is not None:
                await asyncio.sleep(waitForClick / 1000)
            await self.page.mouse.up()
        except Exception as exc:
            logger.debug("Warning: could not click mouse, error message: %s", exc)

        await asyncio.sleep(random.random() * 2)
        self.toggleRandomMove(True)

    async def move(
        self,
        selector: Union[str, ElementHandle],
        paddingPercentage: Optional[float] = None,
        waitForSelector: Optional[float] = None,
    ):
        self.toggleRandomMove(False)
        elem = None
        if isinstance(selector, str):
            if "//" in selector:
                if waitForSelector:
                    await self.page.waitForXpath(timeout=waitForSelector)
                elem = (await self.page.xpath(selector))[0]
            else:
                if waitForSelector:
                    await self.page.waitForSelector(timeout=waitForSelector)
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
        box = await getElementBox(self.page, elem)
        if box is None:
            raise Exception(
                "Could not find the dimensions of the element you're clicking on, this might be a bug?"
            )
        destination = getRandomBoxPoint(box, paddingPercentage)
        dimensions = {"height": box["height"], "width": box["width"]}
        overshooting = shouldOvershoot(self.previous, destination)
        to = (
            overshoot(destination, self.overshootRadius)
            if overshooting
            else destination
        )
        await self.tracePath(path(self.previous, to))

        if overshooting:
            boundingBox = {
                "height": dimensions["height"],
                "width": dimensions["width"],
                "x": destination.x,
                "y": destination.y,
            }
            correction = path(to, boundingBox, self.overshootSpread)
            await self.tracePath(correction)
        self.previous = destination
        self.toggleRandomMove(True)

    async def moveTo(self, destination: dict) -> Coroutine[None, None, None]:
        destinationVector = Vector(destination["x"], destination["y"])
        self.toggleRandomMove(False)
        await self.tracePath(path(self.previous, destinationVector))
        self.toggleRandomMove(True)


def createCursor(
    page, start: Union[Vector, Dict] = origin, performRandomMoves: bool = False
) -> Coroutine[None, None, GhostCursor]:
    if isinstance(start, dict):
        start = Vector(**start)
    cursor = GhostCursor(page, start)
    if performRandomMoves:
        # Start random mouse movements. Do not await the promise but return immediately
        asyncio.ensure_future(cursor.randomMove())  # fire and forget
    return cursor


def get_path(start: Dict, end: Dict) -> List[Dict]:
    vectors = path(Vector(**start), Vector(**end))
    return [el.__dict__ for el in vectors]
