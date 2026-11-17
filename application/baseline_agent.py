"""Baseline Direct Code Generation Agent (for comparison).

This implements a simple LLM-based system WITHOUT interface library:
- Generates fresh Python code for every query
- No interface reuse
- No semantic retrieval
- No parameter inheritance

Used as baseline to measure the advantage of the interface-based approach.
"""

from __future__ import annotations

import json
import logging
import re
import time
import traceback
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from openai import OpenAI

from config import settings
from model.tools import _load_data, get_dataset_schema, get_ticker_mapping

logger = logging.getLogger(__name__)
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class BaselineAgent:
    """Direct code generation without interface library (baseline for comparison)."""
    
    def __init__(self) -> None:
        api_key = settings.groq_api_key
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in .env")
        self.client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
        self.model = settings.groq_model

    def process_query(self, query: str) -> dict[str, Any]:
        """Generate and execute fresh code for every query."""
        start = time.perf_counter()
        
        schema = get_dataset_schema()
        ticker_mapping = get_ticker_mapping()
        
        # Generate code from scratch every time
        system = f"""You are a Python data analyst. Generate complete Python code to answer the user's query.

{schema}

TICKER MAPPING:
{ticker_mapping}

IMPORTANT:
- Import all modules INSIDE the generated code
- Use df = _load_data() to get the dataset
- Return a dict result
- For charts: save to settings.charts_dir, call plt.close(fig), include "chart_path" in result
- Handle errors gracefully

Respond with ONLY valid JSON:
{{
  "code": "import pandas as pd\\nimport matplotlib.pyplot as plt\\n...\\nresult = {{'value': 123}}",
  "description": "what this code does"
}}
"""

        try:
            # Generate code
            gen_start = time.perf_counter()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Query: {query}"}
                ],
                temperature=0.1,
                max_tokens=1500,
            )
            gen_time = (time.perf_counter() - gen_start) * 1000
            
            content = response.choices[0].message.content.strip()
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            
            # Parse JSON
            if "```" in content:
                match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
                if match:
                    content = match.group(1).strip()
            spec = json.loads(content)
            code = spec["code"]
            
            # Execute code
            exec_start = time.perf_counter()
            result = self._execute_code(code)
            exec_time = (time.perf_counter() - exec_start) * 1000
            
            error = result.get("error")
            output = result.get("result") or {}
            
            latency_ms = (time.perf_counter() - start) * 1000
            
            # Synthesize answer
            if error:
                answer = f"⚠️ Execution error: {error}"
            else:
                answer = f"Generated and executed fresh code. Result: {json.dumps(output, default=str)}"
            
            return {
                "answer": answer,
                "result": output,
                "error": error,
                "has_error": bool(error),
                "latency_ms": latency_ms,
                "generation_time_ms": gen_time,
                "execution_time_ms": exec_time,
                "token_usage": token_usage,
                "chart_path": output.get("chart_path") if isinstance(output, dict) else None,
            }
            
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            error_msg = f"{type(e).__name__}: {str(e)[-200:]}"
            logger.error("Baseline agent failed: %s", error_msg)
            return {
                "answer": f"⚠️ Code generation failed: {error_msg}",
                "result": None,
                "error": error_msg,
                "has_error": True,
                "latency_ms": latency_ms,
                "generation_time_ms": 0,
                "execution_time_ms": 0,
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "chart_path": None,
            }

    def _execute_code(self, code: str) -> dict[str, Any]:
        """Execute generated code in a sandboxed environment."""
        try:
            namespace: dict[str, Any] = {
                "pd": pd,
                "np": np,
                "plt": plt,
                "matplotlib": matplotlib,
                "Path": Path,
                "settings": settings,
                "_load_data": _load_data,
                "logger": logger,
                "__builtins__": __builtins__,
            }
            
            exec(compile(code, "<generated>", "exec"), namespace)
            
            # Look for 'result' variable in namespace
            if "result" in namespace:
                result = namespace["result"]
                if isinstance(result, dict):
                    return {"result": result, "error": None}
                else:
                    return {"result": {"value": result}, "error": None}
            else:
                return {"result": {}, "error": None}
                
        except Exception as e:
            return {"result": None, "error": f"{type(e).__name__}: {str(e)[-200:]}"}


# Singleton
baseline_agent = BaselineAgent()
