import logging

from pyppeteer_ghost_cursor.spoof import createCursor, get_path as path
from pyppeteer_ghost_cursor.mouseHelper import installMouseHelper

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

_logger.warning(
    "DEPRECATION WARNING: pyppeteer_ghost_cursor IS NO LONGER ACTIVE! Please use python_ghost_cursor (https://pypi.org/project/python-ghost-cursor/) instead."
)
