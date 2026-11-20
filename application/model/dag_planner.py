"""DAG Planner - Generates multi-step execution plans for complex queries.

The DAG planner decomposes complex queries into multiple atomic steps,
identifies dependencies, and enables parallel execution where possible.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI

from config import settings
from model.tools import interface_library, get_dataset_schema, get_ticker_mapping

logger = logging.getLogger(__name__)
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class DAGPlanner:
    """Plans multi-step execution workflows using LLM."""

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

    def should_use_dag(self, query: str) -> tuple[bool, int]:
        """
        Determine if query is complex enough to benefit from DAG execution.
        
        Returns:
            (should_use_dag: bool, complexity_score: int)
        """
        # Heuristics for complexity
        complexity_indicators = [
            (r"compare.*and.*and", 3),  # Multiple comparisons (3+ items)
            (r"\bthen\b", 2),  # Sequential operations
            (r"after that", 2),
            (r"also", 1),
            (r"calculate.*then.*plot", 3),  # Multi-step analysis
            (r"calculate.*then.*show", 3),
            (r"calculate.*and.*show", 2),
            (r"calculate.*and.*plot", 2),
            (r"find.*best.*and.*show", 3),
            (r"find.*\w+.*and.*plot", 3),
            (r"for each", 2),  # Iteration
            (r"all.*stocks", 2),  # Batch operations
            (r"compare.*calculate", 2),  # Compare + calculation
            (r"get.*calculate.*show", 3),  # 3-step: fetch, calculate, visualize
            (r"get.*then.*calculate", 2),  # Explicit sequence
        ]
        
        score = 0
        query_lower = query.lower()
        
        for pattern, weight in complexity_indicators:
            if re.search(pattern, query_lower):
                score += weight
                logger.debug(f"Pattern matched: {pattern} (weight={weight})")
        
        # Count commas (often indicate multiple requirements)
        comma_count = query_lower.count(",")
        score += min(comma_count, 2)  # Max 2 points from commas
        
        logger.info(f"Query complexity score: {score} (threshold={settings.dag_complexity_threshold})")
        
        # Threshold: score >= 3 suggests DAG would help
        should_use = score >= settings.dag_complexity_threshold
        return (should_use, score)

    def generate_dag(
        self,
        query: str,
        available_interfaces: list[dict[str, str]],
    ) -> dict[str, Any]:
        """
        Generate a multi-step execution DAG for a complex query.
        
        Returns:
            {
              "use_dag": bool,
              "steps": [
                {
                  "id": int,
                  "interface": str,
                  "args": dict,
                  "depends_on": list[int],
                  "description": str
                }
              ],
              "token_usage": dict
            }
        """
        
        # Format available interfaces (limit to top 10 to save tokens)
        interfaces_desc = "\n".join([
            f"- {iface['name']}: {iface['description']}"
            for iface in available_interfaces[:10]
        ]) if available_interfaces else "None"
        
        system = f"""Plan multi-step execution for stock queries.

DATA: indian_stocks.csv (Date, Ticker, Open, High, Low, Close, Volume)
TICKERS: TCS.NS, INFY.NS, WIPRO.NS, RELIANCE.NS, HDFCBANK.NS

Available Interfaces (top 10):
{interfaces_desc}

RULES:
1. Break query into ATOMIC steps (each does ONE thing)
2. Reuse interfaces when possible, use "CREATE_NEW" for new operations
3. Max 4 steps (keep it simple)
4. Reference previous results: {{"arg": "$step1.ticker"}}

OUTPUT (JSON only):
{{"use_dag": true, "steps": [{{"id": 1, "interface": "name_or_CREATE_NEW", "args": {{}}, "depends_on": [], "description": "what this step does"}}]}}

If single operation: {{"use_dag": false, "reason": "Single step sufficient"}}

JSON only, no explanation."""

        try:
            content, token_usage = self._llm(
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Query: {query}"}
                ],
                temperature=0.1,
                max_tokens=1500,
            )
            
            dag = self._parse_json(content)
            dag["token_usage"] = token_usage
            
            # Validate DAG structure
            if dag.get("use_dag"):
                self._validate_dag(dag)
            
            return dag
            
        except Exception as e:
            logger.error("DAG generation failed: %s", e)
            return {
                "use_dag": False,
                "reason": f"DAG generation error: {e}",
                "token_usage": {"total_tokens": 0}
            }

    def _validate_dag(self, dag: dict) -> None:
        """Validate DAG structure for common errors."""
        steps = dag.get("steps", [])
        
        if not steps:
            raise ValueError("DAG has no steps")
        
        step_ids = {step["id"] for step in steps}
        
        for step in steps:
            # Check required fields
            required = ["id", "interface", "args", "depends_on", "description"]
            for field in required:
                if field not in step:
                    raise ValueError(f"Step {step.get('id')} missing field: {field}")
            
            # Check dependency validity
            for dep_id in step["depends_on"]:
                if dep_id not in step_ids:
                    raise ValueError(f"Step {step['id']} depends on non-existent step {dep_id}")
                if dep_id >= step["id"]:
                    raise ValueError(f"Step {step['id']} has circular or forward dependency on {dep_id}")

    @staticmethod
    def _parse_json(content: str) -> dict[str, Any]:
        """Parse JSON from LLM response."""
        if "```" in content:
            match = re.search(r"```(?:json)?\s*(.*?)```", content, re.DOTALL)
            if match:
                content = match.group(1).strip()
        return json.loads(content)


# Singleton
dag_planner = DAGPlanner()
