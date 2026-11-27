"""Dynamic Interface Library — LLM-generated and auto-tested Python functions.

No hardcoded tools. The LLM generates new interfaces on demand when a query
cannot be resolved by existing ones. Each generated function is auto-tested
against the dataset before being added to the library.

This implements Phase 1 of the research paper:
- Self-Exploration Engine
- Interface Code Drafter
- Compiler Feedback Loop
- Semantic Merger (via FAISS deduplication)
"""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Any, Callable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from config import settings
from logger import get_logger, sanitize_args, truncate_payload

logger = get_logger(__name__)

# ── Dataset loader ──────────────────────────────────────────────────
_df_cache: pd.DataFrame | None = None


def _load_data() -> pd.DataFrame:
    global _df_cache
    if _df_cache is None:
        path = settings.dataset_path
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found at {path}")
        _df_cache = pd.read_csv(path, parse_dates=["Date"])
        logger.info("Loaded dataset: %s rows=%d tickers=%d",
                    path, len(_df_cache), _df_cache["Ticker"].nunique())
    return _df_cache


def get_dataset_schema() -> str:
    """Return a description of the dataset for the LLM to reason about."""
    df = _load_data()
    tickers = sorted(df["Ticker"].unique().tolist())
    date_min = str(df["Date"].min().date())
    date_max = str(df["Date"].max().date())
    
    return (
        f"Dataset: indian_stocks.csv\n"
        f"Columns: {list(df.columns)}\n"
        f"Rows: {len(df)}\n"
        f"Date range: {date_min} to {date_max} (historical data only, no future projections)\n"
        f"Available tickers (NSE): {tickers}\n"
        f"The dataset is loaded as a pandas DataFrame called `df`.\n"
        f"IMPORTANT: Data is only available from {date_min} to {date_max}. If user asks for dates outside this range, use the closest available dates.\n"
        f"Always use the exact .NS ticker format when filtering or querying.\n"
        f"Charts should be saved to: {settings.charts_dir}\n"
        f"Use matplotlib with Agg backend. Always call plt.close(fig) after saving.\n"
        f"Return a dict. If a chart is generated, include 'chart_path' key with the full path string."
    )


def get_ticker_mapping() -> str:
    """Return ticker mapping reference for LLM prompts."""
    mapping = {
        "TCS": "TCS.NS",
        "Reliance": "RELIANCE.NS",
        "Infosys": "INFY.NS",
        "INFY": "INFY.NS",
        "HDFC Bank": "HDFCBANK.NS",
        "ICICI Bank": "ICICIBANK.NS",
        "SBI": "SBIN.NS",
        "Wipro": "WIPRO.NS",
        "HCL": "HCLTECH.NS",
        "Maruti": "MARUTI.NS",
        "Sun Pharma": "SUNPHARMA.NS",
        "Bajaj Finance": "BAJFINANCE.NS",
        "Asian Paints": "ASIANPAINT.NS",
        "HUL": "HINDUNILVR.NS",
        "L&T": "LT.NS",
        "Airtel": "BHARTIARTL.NS",
        "ITC": "ITC.NS",
        "Adani": "ADANIENT.NS",
        "Tata Steel": "TATASTEEL.NS",
        "Dr Reddy": "DRREDDY.NS",
    }
    return "\n".join(f"  {name} → {ticker}" for name, ticker in mapping.items())


# ── Dynamic Interface Library ───────────────────────────────────────

class InterfaceLibrary:
    """
    Stores LLM-generated Python functions as the runtime tool library.
    Functions are stored both in memory and persisted to registry.json.
    """

    REGISTRY_PATH = Path(__file__).parent / "registry.json"

    def __init__(self) -> None:
        # name -> {code, description, test_query, created_at, call_count}
        self._registry: dict[str, dict[str, Any]] = {}
        # name -> compiled callable
        self._functions: dict[str, Callable] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Load persisted interfaces from registry.json."""
        if self.REGISTRY_PATH.exists():
            try:
                data = json.loads(self.REGISTRY_PATH.read_text(encoding="utf-8"))
                for name, entry in data.items():
                    try:
                        self._compile_and_register(name, entry["code"], entry)
                        logger.info("Loaded persisted interface: %s", name)
                    except Exception as e:
                        logger.warning("Failed to load interface %s: %s", name, e)
            except Exception as e:
                logger.warning("Failed to load registry: %s", e)

    def _save_registry(self) -> None:
        """Persist registry metadata (not callables) to registry.json."""
        data = {
            name: {k: v for k, v in entry.items() if k != "callable"}
            for name, entry in self._registry.items()
        }
        self.REGISTRY_PATH.write_text(
            json.dumps(data, indent=2, default=str), encoding="utf-8"
        )

    def _compile_and_register(
        self, name: str, code: str, metadata: dict[str, Any]
    ) -> None:
        """Compile a code string and store the callable."""
        namespace: dict[str, Any] = {
            "pd": pd, "np": np, "plt": plt, "matplotlib": matplotlib,
            "Path": Path, "settings": settings,
            "_load_data": _load_data, "logger": logger,
            "__builtins__": __builtins__,
        }
        exec(compile(code, f"<interface:{name}>", "exec"), namespace)
        if name not in namespace:
            raise ValueError(f"Function '{name}' not found in generated code")
        self._functions[name] = namespace[name]
        self._registry[name] = {**metadata, "code": code}

    def add(
        self,
        name: str,
        code: str,
        description: str,
        test_query: str = "",
    ) -> None:
        """Add a new LLM-generated interface to the library."""
        import datetime
        self._compile_and_register(name, code, {
            "description": description,
            "test_query": test_query,
            "created_at": datetime.datetime.now().isoformat(),
            "call_count": 0,
        })
        self._save_registry()
        logger.info("Added new interface to library: %s", name)

    def execute(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a registered interface and return the result."""
        if name not in self._functions:
            logger.error("Tool invocation failed: interface '%s' not found in library", name)
            return {"error": f"Interface '{name}' not found in library"}

        start = time.perf_counter()
        logger.info("Tool invoke | name=%s | args=%s", name, sanitize_args(args))
        try:
            self._registry[name]["call_count"] = \
                self._registry[name].get("call_count", 0) + 1
            self._save_registry()
            result = self._functions[name](**args)
            duration_ms = (time.perf_counter() - start) * 1000
            if result is None or result == {}:
                logger.warning("Tool returned empty result | name=%s | duration=%.1fms", name, duration_ms)
            else:
                logger.info("Tool completed | name=%s | duration=%.1fms", name, duration_ms)
                logger.debug("Tool result | name=%s | output=%s", name, truncate_payload(result, 500))
            return {"result": result, "error": None}
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception("Tool error | name=%s | duration=%.1fms | error=%s", name, duration_ms, e)
            return {"result": None, "error": f"{type(e).__name__}: {e}"}

    def list_all(self) -> list[dict[str, Any]]:
        """Return metadata for all registered interfaces."""
        return [
            {
                "name": name,
                "description": entry.get("description", ""),
                "code": entry.get("code", ""),
                "test_query": entry.get("test_query", ""),
                "created_at": entry.get("created_at", ""),
                "call_count": entry.get("call_count", 0),
            }
            for name, entry in self._registry.items()
        ]

    def get_descriptions(self) -> list[dict[str, str]]:
        """Return name + description for FAISS indexing."""
        return [
            {"name": name, "description": entry.get("description", "")}
            for name, entry in self._registry.items()
        ]

    def has(self, name: str) -> bool:
        return name in self._functions

    def clear(self) -> None:
        """Clear all interfaces (for testing)."""
        self._registry.clear()
        self._functions.clear()
        if self.REGISTRY_PATH.exists():
            self.REGISTRY_PATH.unlink()


# Singleton
interface_library = InterfaceLibrary()
