"""Executor — delegates to the dynamic InterfaceLibrary."""

from __future__ import annotations

import time
from typing import Any

from logger import get_logger, sanitize_args, truncate_payload
from model.tools import interface_library

logger = get_logger(__name__)


class Executor:
    def execute(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        start = time.perf_counter()
        logger.debug("Executing interface '%s' | args=%s", name, sanitize_args(args))
        output = interface_library.execute(name, args)
        duration_ms = (time.perf_counter() - start) * 1000
        status = "failure" if output.get("error") else "success"
        logger.info(
            "Executor finished | interface=%s | status=%s | duration=%.1fms",
            name,
            status,
            duration_ms,
        )
        if output.get("error"):
            logger.warning("Executor error | interface=%s | error=%s", name, truncate_payload(output.get("error"), 500))
        else:
            logger.debug("Executor result | interface=%s | result=%s", name, truncate_payload(output.get("result"), 500))
        return output
