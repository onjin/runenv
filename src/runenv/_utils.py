from __future__ import annotations

import logging


def add_stdout_handler(verbosity: int) -> None:
    v_map = {1: logging.ERROR, 2: logging.INFO, 3: logging.DEBUG}
    level = v_map.get(verbosity, 1)
    logging.basicConfig(level=level)
