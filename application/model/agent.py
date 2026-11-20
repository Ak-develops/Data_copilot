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
        # Extract function signature from the interface code if available
        interface_sig = ""
        if candidate:
            try:
                from model.tools import interface_library
                interface_code = interface_library._registry.get(candidate["name"], {}).get("code", "")
                # Extract first line of function definition
                for line in interface_code.split("\n"):
                    if line.strip().startswith("def "):
                        interface_sig = line.strip()
                        break
            except:
                pass
        
        existing_desc = (
            f"Existing interface: `{candidate['name']}` — {candidate['description']}\n"
            f"Function signature: {interface_sig if interface_sig else 'Unknown - only use ticker parameter'}\n"
            f"Similarity score: {similarity_score:.2f} (1.0 = perfect match, 0.0 = no match)\n\n"
            f"⚠️ CRITICAL: Only pass parameters that exist in the function signature above!"
            if candidate else "No existing interface found."
        )

        system = f"""You decide how to answer stock queries.

DATASET: indian_stocks.csv (Date, Ticker, Open, High, Low, Close, Volume)
DATA AVAILABLE: 2022-01-01 to 2024-12-31 (NO 2025 or 2026 data!)

CRITICAL TICKER FORMAT:
- All tickers MUST use .NS suffix (NSE stocks)
- "TCS" → "TCS.NS"
- "Infosys" or "INFY" → "INFY.NS"
- "Wipro" → "WIPRO.NS"
- "Reliance" → "RELIANCE.NS"
- "HDFC Bank" or "HDFCBANK" → "HDFCBANK.NS"
- "ICICI Bank" or "ICICIBANK" → "ICICIBANK.NS"
- "ITC" → "ITC.NS"
- "SBI" or "State Bank" → "SBIN.NS"
- "HCL Tech" or "HCL" → "HCLTECH.NS"
- "Asian Paints" → "ASIANPAINT.NS"

{existing_desc}

CRITICAL PARAMETER MATCHING:
- You MUST use ONLY the parameters that the interface accepts
- DO NOT add extra parameters (like 'year' if interface doesn't have it)
- DO NOT rename parameters
- If interface signature doesn't match query needs, choose action=create instead

Example:
- Interface: get_current_price(ticker: str)
- Query: "current price of TCS in 2024"
- CORRECT: action=reuse, args={{"ticker": "TCS.NS"}}  (ignore year, interface doesn't need it)
- WRONG: action=reuse, args={{"ticker": "TCS.NS", "year": 2024}}  (adds non-existent parameter!)

CRITICAL REUSE RULES:
- Score >= 0.35: YOU MUST REUSE (almost identical functionality)
- Score >= 0.25: STRONGLY PREFER reuse unless fundamentally impossible  
- Score >= 0.20: Try to reuse by adapting parameters
- Score < 0.20: Create new only if truly necessary

WHEN TO REUSE:
✓ Different tickers but same operation → REUSE
✓ Different dates but same calculation → REUSE
✓ Different window (50-day vs 200-day MA) but same concept → REUSE
✓ Different number of stocks but same comparison → REUSE
✓ Similar intent (e.g., "current price", "latest price", "price today") → REUSE
✓ Query asks for data the interface can provide → REUSE
✓ "Show chart", "plot", "visualize" + stock → REUSE plot_stock_trend
✓ "Get data", "show data", "stock data" + chart → REUSE plot_stock_trend
✓ ANY query about showing/plotting single stock price → REUSE plot_stock_trend

WHEN TO CREATE:
✗ User wants bar chart but interface only makes line charts
✗ User wants volatility but interface only does returns
✗ Completely different analysis type

CRITICAL YEAR EXTRACTION:
- If query mentions "2022", "2023", or "2024", extract that year
- If no year mentioned, use latest available (2024)
- NEVER use 2025 or 2026 (no data!)

OUTPUT (JSON only):
Reuse: {{"action": "reuse", "interface_name": "<name>", "args": {{"ticker": "TCS.NS", "year": 2024}}}}
Create: {{"action": "create", "interface_name": null, "args": null}}

ALWAYS use .NS suffix for tickers and correct year (2022-2024)! RESPOND ONLY WITH JSON. NO EXPLANATIONS."""

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
        total_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        system = f"""You are a Python data analyst. Write a function for the user's stock query.

DATASET: indian_stocks.csv with columns: Date, Ticker, Open, High, Low, Close, Volume
DATA RANGE: 2022-01-01 to 2024-12-31 (NO 2025 or 2026 data!)

CRITICAL TICKER FORMAT (MUST USE .NS SUFFIX):
"TCS" → "TCS.NS"
"Infosys"/"INFY" → "INFY.NS"
"Wipro" → "WIPRO.NS"
"Reliance" → "RELIANCE.NS"
"HDFC Bank"/"HDFCBANK" → "HDFCBANK.NS"
"ICICI Bank"/"ICICIBANK" → "ICICIBANK.NS"
"ITC" → "ITC.NS"
"SBI"/"State Bank" → "SBIN.NS"
"HCL Tech"/"HCL" → "HCLTECH.NS"
"Asian Paints" → "ASIANPAINT.NS"

RULES:
1. Function name: GENERIC lowercase verb (get_, plot_, compare_, calculate_)
   ❌ BAD: plot_tcs_50day_ma, get_bajaj_finance_range
   ✅ GOOD: plot_moving_average, get_price_range
2. Use PARAMETERS for specificity, NOT function names
   ❌ BAD: def get_tcs_price() - hardcoded company
   ✅ GOOD: def get_current_price(ticker: str) - parameterized
3. Import ALL modules INSIDE the function:
   from config import settings
   import pandas as pd
   import matplotlib.pyplot as plt
4. Load data: df = _load_data()
5. ALWAYS use .NS suffix for ticker parameters
6. ALWAYS use years 2022-2024 only (default to 2024)
7. Charts: save to settings.charts_dir/"file.png", call plt.close(fig), return {{"chart_path": ...}}
8. Always return a dict
9. Handle missing tickers with try/except

NAMING EXAMPLES:
Query: "Plot 50-day MA for TCS" → name="plot_moving_average", args={{"ticker":"TCS.NS", "window":50}}
Query: "Bajaj Finance 2024 range" → name="get_price_range", args={{"ticker":"BAJFINANCE.NS", "weeks":52}}
Query: "Compare TCS vs Infosys" → name="compare_two_stocks", args={{"ticker1":"TCS.NS", "ticker2":"INFY.NS"}}

OUTPUT (valid JSON only):
{{
  "name": "function_name",
  "description": "brief description",
  "code": "def function_name(...):\\n    import pandas as pd\\n    ...",
  "args": {{"ticker": "TCS.NS", "year": 2024}},
  "test_args": {{"ticker": "TCS.NS", "year": 2024}}
}}

CRITICAL: Use .NS suffix and year 2022-2024 in ALL args/test_args! Respond ONLY with JSON."""

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
                    # Feed error back to LLM for self-correction (limit to 200 chars to avoid token explosion)
                    short_error = error_msg[:200] if len(error_msg) > 200 else error_msg
                    system += f"\n\nPrevious attempt FAILED with: {short_error}\nFix this bug. Check imports and JSON syntax."

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
        
        # Truncate large results to avoid 413 errors
        result_str = json.dumps(result, indent=2, default=str)
        if len(result_str) > 1000:
            # Keep only keys and first 500 chars of result
            truncated_result = {k: str(v)[:100] + "..." if len(str(v)) > 100 else v 
                               for k, v in list(result.items())[:5]}
            result_str = json.dumps(truncated_result, indent=2, default=str)
        
        system = """You are a stock analysis assistant. Summarize the tool result clearly and concisely.
- Use bullet points for structured data
- Include specific numbers (prices, percentages)
- Keep it under 6 lines
- Be direct and factual"""

        user_content = (
            f"Query: {query}\n"
            f"Interface used: {interface_name}{new_note}\n"
            f"Args: {json.dumps(args, default=str)[:200]}\n"
            f"Result: {result_str}"
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
            # Fallback: return simple summary without LLM
            if "chart_path" in result:
                return f"✅ Generated chart: {result['chart_path']}", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return json.dumps(result, indent=2, default=str)[:500], {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # ── JSON parsing ───────────────────────────────────────────────

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        if "```" in content:
            match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
            if match:
                content = match.group(1).strip()
        return json.loads(content)
