"""Agent orchestrator — LLM-based interface selection AND generation.

Two modes:
1. REUSE — query matches an existing interface → extract args and call it
2. CREATE — no match → LLM writes a new Python function, auto-tests it,
            adds it to the Interface Library, then executes it

This implements the full Phase 1 + Phase 2 loop from the research paper.
"""

from __future__ import annotations

import json
import logging
import re
import traceback
from typing import Any

from openai import OpenAI

from config import settings
from model.tools import interface_library, get_dataset_schema, get_ticker_mapping

logger = logging.getLogger(__name__)
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class Agent:
    def __init__(self) -> None:
        api_key = settings.groq_api_key
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in .env")
        self.client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
        self.model = settings.groq_model

    def _llm(self, messages: list[dict], temperature: float = 0.1,
             max_tokens: int = 1000) -> tuple[str, dict[str, int]]:
        """Call the LLM and return the response content + token usage."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body={"tool_choice": "none"},
        )
        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        return response.choices[0].message.content.strip(), token_usage

    # ── Step 1: Decide — reuse or create ──────────────────────────

    def decide(
        self,
        query: str,
        candidate: dict[str, str] | None,
        similarity_score: float | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """
        Given a query and the best matching existing interface (or None),
        ask the LLM: should we reuse it or create a new one?

        Returns:
            {
              "action": "reuse" | "create",
              "interface_name": str | None,
              "args": dict | None,
            }
        """
        schema = get_dataset_schema()
        existing_desc = (
            f"Existing interface: `{candidate['name']}` — {candidate['description']}\n"
            f"Similarity score: {similarity_score:.2f} (1.0 = perfect match, 0.0 = no match)"
            if candidate else "No existing interface found."
        )

        system = f"""You are an AI agent that decides how to answer stock analysis queries.

Dataset schema:
{schema}

{existing_desc}

DECISION RULES:
- If similarity score >= 0.50: STRONGLY prefer reuse (unless fundamentally incompatible)
- If similarity score >= 0.35: Reuse if the existing interface can be adapted with different parameters
- If no interface exists (score < 0.35) or existing one is fundamentally incompatible: create new

Examples of REUSABLE scenarios:
✓ "plot TCS and Wipro for 2024" → reuse "plot_stock_comparison" (different tickers/dates)
✓ "show me average values for 3 stocks" → reuse "plot_average_stock_values" (different tickers)
✓ "what's the price of Reliance" → reuse "get_latest_closing_price" (different ticker)

Examples of CREATE NEW scenarios:
✗ User wants "moving average" but only "latest price" interface exists (different calculation)
✗ User wants "bar chart" but only "line chart" interface exists (different visualization)

Respond with ONLY valid JSON in one of these two formats:

For reuse:
{{"action": "reuse", "interface_name": "<name>", "args": {{...}}}}

For create:
{{"action": "create", "interface_name": null, "args": null}}

Do NOT output anything except the JSON."""

        messages = [{"role": "system", "content": system}]
        if history:
            for turn in history[-4:]:
                messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": query})

        try:
            content, token_usage = self._llm(messages, temperature=0.1)
            result = self._parse_json(content)
            result["token_usage"] = token_usage
            return result
        except Exception as e:
            logger.error("decide() failed: %s", e)
            return {"action": "create", "interface_name": None, "args": None, "token_usage": {"total_tokens": 0}}

    # ── Step 2: Generate a new interface ──────────────────────────

    def generate_interface(self, query: str) -> dict[str, Any]:
        """
        Ask the LLM to write a new Python function that answers the query.
        Auto-tests it up to 3 times. Returns the generated interface metadata.

        Returns:
            {
              "success": bool,
              "name": str,
              "code": str,
              "description": str,
              "args": dict,
              "error": str | None,
              "token_usage": dict,
            }
        """
        schema = get_dataset_schema()
        ticker_mapping = get_ticker_mapping()
        total_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        system = f"""You are an expert Python data analyst. Write a Python function that answers the user's stock analysis query.

{schema}

TICKER MAPPING (user-friendly names to NSE tickers):
{ticker_mapping}

IMPORTANT: Always convert user-friendly names to their .NS ticker symbols (e.g., "Infosys" → "INFY.NS", not "INFOSYS.NS").

CODE GENERATION RULES:
1. The function MUST be named starting with a lowercase verb (e.g., get_, plot_, compare_, calculate_, show_)
2. Use typed parameters with defaults where sensible
3. CRITICAL: Import all required modules INSIDE the function body, before using them:
   - from config import settings
   - import pandas as pd
   - import matplotlib.pyplot as plt
   - etc.
4. Get the dataframe using: df = _load_data()
5. For charts: use matplotlib, save to settings.charts_dir / "filename.png", call plt.close(fig), include "chart_path" in the return dict
6. Always return a dict (never return None or other types)
7. Include error handling for missing tickers or empty dataframes
8. Use ONLY these pre-available names: _load_data, logger, pd, np, plt, Path, settings (import others inside the function)

JSON OUTPUT FORMAT (MUST be valid JSON, no trailing commas, properly escaped strings):
{{
  "name": "function_name",
  "description": "one sentence describing what this function does",
  "code": "def function_name(...):\\n    from config import settings\\n    import pandas as pd\\n    ...",
  "args": {{"param1": "value1", ...}},
  "test_args": {{"param1": "test_value1", ...}}
}}

The "args" should be the actual arguments to call the function with for this specific query.
The "test_args" should be safe test arguments (use real tickers like TCS.NS, RELIANCE.NS, INFY.NS).
Respond with ONLY valid JSON. Do NOT include anything outside the JSON."""

        for attempt in range(3):
            try:
                content, token_usage = self._llm(
                    [
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"Query: {query}"},
                    ],
                    temperature=0.1 + attempt * 0.05,  # Lower temperature for more deterministic code
                    max_tokens=1200,
                )
                
                # Accumulate token usage
                total_token_usage["prompt_tokens"] += token_usage.get("prompt_tokens", 0)
                total_token_usage["completion_tokens"] += token_usage.get("completion_tokens", 0)
                total_token_usage["total_tokens"] += token_usage.get("total_tokens", 0)
                
                spec = self._parse_json(content)
                name = spec["name"]
                code = spec["code"]
                description = spec["description"]
                args = spec["args"]
                test_args = spec.get("test_args", args)

                # ── Compiler Feedback Loop: auto-test ─────────────
                test_result = self._test_function(name, code, test_args)
                if test_result["success"]:
                    logger.info("Generated interface '%s' passed tests (attempt %d)",
                                name, attempt + 1)
                    return {
                        "success": True,
                        "name": name,
                        "code": code,
                        "description": description,
                        "args": args,
                        "error": None,
                        "token_usage": total_token_usage,
                    }
                else:
                    error_msg = test_result["error"]
                    logger.warning(
                        "Interface '%s' failed test (attempt %d): %s",
                        name, attempt + 1, error_msg
                    )
                    # Feed error back to LLM for self-correction
                    system += f"\n\nPrevious attempt FAILED with: {error_msg}\nFix this bug in the next attempt. Make sure to import all modules and check your JSON syntax."

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)[-200:]}"
                logger.error("generate_interface attempt %d failed: %s", attempt + 1, error_msg)

        return {
            "success": False,
            "name": None,
            "code": None,
            "description": None,
            "args": None,
            "error": "Failed to generate a working interface after 3 attempts",
            "token_usage": total_token_usage,
        }

    def _test_function(self, name: str, code: str, test_args: dict) -> dict[str, Any]:
        """Compile and run the function with test args to verify it works."""
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            import pandas as pd
            import numpy as np
            from pathlib import Path
            from config import settings

            namespace: dict[str, Any] = {
                "pd": pd, "np": np, "plt": plt, "matplotlib": matplotlib,
                "Path": Path, "settings": settings,
                "_load_data": __import__(
                    "model.tools", fromlist=["_load_data"]
                )._load_data,
                "logger": logger,
                "__builtins__": __builtins__,
            }
            exec(compile(code, f"<test:{name}>", "exec"), namespace)
            if name not in namespace:
                return {"success": False, "error": f"Function '{name}' not defined"}
            result = namespace[name](**test_args)
            if not isinstance(result, dict):
                return {"success": False, "error": "Function must return a dict"}
            if "error" in result and result["error"]:
                return {"success": False, "error": result["error"]}
            return {"success": True, "result": result}
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            # Only return last 500 chars of traceback to avoid overwhelming the LLM
            return {"success": False, "error": error_msg[-500:]}

    # ── Step 3: Synthesize natural language answer ─────────────────

    def synthesize_answer(
        self,
        query: str,
        interface_name: str | None,
        args: dict | None,
        result: dict,
        is_new: bool = False,
    ) -> tuple[str, dict[str, int]]:
        """Generate a concise natural-language summary of the tool result. Returns (answer, token_usage)."""
        if "error" in result and result.get("error"):
            return f"⚠️ {result['error']}", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        new_note = " (newly created interface)" if is_new else ""
        system = """You are a stock analysis assistant. Summarize the tool result clearly and concisely.
- Use bullet points for structured data
- Include specific numbers (prices, percentages)
- Keep it under 6 lines
- Be direct and factual"""

        user_content = (
            f"Query: {query}\n"
            f"Interface used: {interface_name}{new_note}\n"
            f"Args: {json.dumps(args, default=str)}\n"
            f"Result: {json.dumps(result, indent=2, default=str)}"
        )
        try:
            content, token_usage = self._llm(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            return content, token_usage
        except Exception as e:
            logger.error("synthesize_answer failed: %s", e)
            return json.dumps(result, indent=2, default=str), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # ── JSON parsing ───────────────────────────────────────────────

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        if "```" in content:
            match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
            if match:
                content = match.group(1).strip()
        return json.loads(content)
