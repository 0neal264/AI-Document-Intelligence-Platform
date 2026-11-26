"""Configure simple application logging without recording document data."""

import logging


def configure_logging() -> None:
    """Set a consistent log format; callers should log events, not document text."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
