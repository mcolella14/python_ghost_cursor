import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

### EXPORTS

from .shared._spoof import get_path as path

# To support deprecations
def createCursor(*args, **kwargs):
    from .pyppeteer import create_cursor

    _logger.warning(
        """DEPRECATION WARNING: 'createCursor' has been moved, please use the new version: 'from python_ghost_cursor.pyppeteer import create_cursor'.
        This method will be removed in a future release.
        """
    )
    if "performRandomMoves" in kwargs:
        kwargs["perform_random_moves"] = kwargs["performRandomMoves"]
        del kwargs["performRandomMoves"]
    return create_cursor(*args, **kwargs)


def installMouseHelper(*args, **kwargs):
    from .pyppeteer import install_mouse_helper

    _logger.warning(
        """DEPRECATION WARNING: 'installMouseHelper' has been moved, please use the new version: 'from python_ghost_cursor.pyppeteer import install_mouse_helper'.
        This method will be removed in a future release.
        """
    )
    return install_mouse_helper(*args, **kwargs)


__all__ = ["path", "createCursor", "installMouseHelper"]
