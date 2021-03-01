import logging

from pyppeteer_ghost_cursor.spoof import createCursor, get_path as path
from pyppeteer_ghost_cursor.mouseHelper import installMouseHelper

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
