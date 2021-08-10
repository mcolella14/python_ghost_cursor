import asyncio
import logging
import time
import random
from typing import Union, Optional, Dict, List
from playwright.sync_api import Page, ElementHandle

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


class GhostCursor:
    def __init__(self, page: Page, start: Vector):
        self.page = page
        self.previous = start
        self.moving = False
        self.overshoot_spread = 10
        self.overshoot_radius = 120
        self.cdp_session = page.context.new_cdp_session(page)

    def get_random_page_point(self) -> Vector:
        """Get a random point on a browser window"""
        target_id = self.page.target._targetId
        window = self.cdp_session.send(
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

    async def random_move(self):
        """Start random mouse movements. Function recursively calls itself"""
        try:
            if not self.moving:
                rand = self.get_random_page_point()
                self.trace_path(path(self.previous, rand), True)
                self.previous = rand
            await asyncio.sleep(random.random() * 2)
            asyncio.ensure_future(
                self.random_move()
            )  # fire and forget, recursive function
        except:
            logger.debug("Warning: stopping random mouse movements")

    def trace_path(self, vectors: List[Vector], abort_on_move: bool = False) -> None:
        """Move the mouse over a number of vectors"""
        for v in vectors:
            try:
                # In case this is called from random mouse movements and the users wants to move the mouse, abort
                if abort_on_move and self.moving:
                    return
                self.page.mouse.move(v.x, v.y)
                self.previous = v
            except Exception as exc:
                # Exit function if the browser is no longer connected
                if not self.page.browser.is_connected():
                    return
                logger.debug("Warning: could not move mouse, error message: %s", exc)

    def toggle_random_move(self, random_: bool):
        self.moving = not random_

    def click(
        self,
        selector: Optional[Union[str, ElementHandle]],
        padding_percentage: Optional[float] = None,
        wait_for_selector: Optional[float] = None,
        wait_for_click: Optional[float] = None,
    ) -> None:
        self.toggle_random_move(False)
        if selector is not None:
            self.move(selector, padding_percentage, wait_for_selector)
            self.toggle_random_move(False)

        try:
            self.page.mouse.down()
            if wait_for_click is not None:
                time.sleep(wait_for_click / 1000)
            self.page.mouse.up()
        except Exception as exc:
            logger.debug("Warning: could not click mouse, error message: %s", exc)

        time.sleep(random.random() * 2)
        self.toggle_random_move(True)

    def move(
        self,
        selector: Union[str, ElementHandle],
        padding_percentage: Optional[float] = None,
        wait_for_selector: Optional[float] = None,
    ) -> None:
        self.toggle_random_move(False)
        elem = None
        if isinstance(selector, str):
            if wait_for_selector:
                self.page.wait_for_selector(selector, timeout=wait_for_selector)
            elem = self.page.query_selector(selector)
            if elem is None:
                raise Exception(
                    'Could not find element with selector "${}", make sure you\'re waiting for the elements with "puppeteer.wait_for_selector"'.format(
                        selector
                    )
                )
        else:  # ElementHandle
            elem = selector

        # Make sure the object is in view
        elem.scroll_into_view_if_needed()
        box = elem.bounding_box()
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
        self.trace_path(path(self.previous, to))

        if overshooting:
            bounding_box = {
                "height": dimensions["height"],
                "width": dimensions["width"],
                "x": destination.x,
                "y": destination.y,
            }
            correction = path(to, bounding_box, self.overshoot_spread)
            self.trace_path(correction)
        self.previous = destination
        self.toggle_random_move(True)

    def move_to(self, destination: dict) -> None:
        destination_vector = Vector(destination["x"], destination["y"])
        self.toggle_random_move(False)
        self.trace_path(path(self.previous, destination_vector))
        self.toggle_random_move(True)


def create_cursor(page, start: Union[Vector, Dict] = origin) -> GhostCursor:
    if isinstance(start, dict):
        start = Vector(**start)
    cursor = GhostCursor(page, start)
    # Can't seem to get random movement to work with Playwright.
    # if perform_random_moves:
    #   asyncio.ensure_future(cursor.random_move()) # fire and forget
    return cursor
