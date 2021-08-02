import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

from .shared import path

# To support deprecations
def createCursor(*args, **kwargs):
    from .pyppeteer import create_cursor

    _logger.warning(
        """DEPRECATION WARNING: 'createCursor' has been moved, please use the new version: 'from python_ghost_cursor.pyppeteer import create_cursor'.
        This method will be removed in a future release.
        """
    )
    return create_cursor(*args, **kwargs)


def installMouseHelper(*args, **kwargs):
    from .pyppeteer import install_mouse_helper

    _logger.warning(
        """DEPRECATION WARNING: 'installMouseHelper' has been moved, please use the new version: 'from python_ghost_cursor.pyppeteer import install_mouse_helper'.
        This method will be removed in a future release.
        """
    )
    return install_mouse_helper(*args, **kwargs)
