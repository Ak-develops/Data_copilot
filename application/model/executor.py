"""Executor — delegates to the dynamic InterfaceLibrary."""

from __future__ import annotations

import logging
from typing import Any

from model.tools import interface_library

logger = logging.getLogger(__name__)


class Executor:
    def execute(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        return interface_library.execute(name, args)
