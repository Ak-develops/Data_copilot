"""Agent service — full dynamic pipeline.

Flow per query:
1. Search Interface Library for a matching existing interface (FAISS)
2. LLM decides: reuse existing OR create new
3. If create: LLM generates code → auto-tests → adds to library
4. Execute the interface
5. Synthesize natural language answer
"""

from __future__ import annotations

import logging
import time
from typing import Any

from config import settings
from model.tools import interface_library, get_dataset_schema
from model.retriever import ToolRetriever
from model.agent import Agent
from model.executor import Executor
from model.dag_planner import dag_planner
from model.dag_executor import dag_executor

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self) -> None:
        self.retriever = ToolRetriever()
        self.agent = Agent()
        self.executor = Executor()
        self._rebuild_index()
        logger.info("AgentService initialized | interfaces=%d", len(interface_library.list_all()))

    def _rebuild_index(self) -> None:
        """Rebuild FAISS index from current library."""
        self.retriever.rebuild(interface_library.get_descriptions())

    def list_tools(self) -> list[dict[str, Any]]:
        """Return all registered interfaces (for /api/tools endpoint)."""
        return [
            {
                "name": i["name"],
                "description": i["description"],
                "parameters": {},
                "code": i.get("code", ""),
                "test_query": i.get("test_query", ""),
                "created_at": i.get("created_at", ""),
                "call_count": i.get("call_count", 0),
            }
            for i in interface_library.list_all()
        ]

    def process_query(
        self,
        query: str,
        routing_mode: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        is_new_interface = False
        total_tokens = 0  # Track total token usage
        use_dag = False  # Track if DAG was used
        
        # ── Step 0: Check if query needs DAG execution ─────────
        should_use_dag, complexity_score = dag_planner.should_use_dag(query)
        
        if should_use_dag and settings.enable_dag_execution:
            logger.info("Query complexity score: %d - attempting DAG execution", complexity_score)
            
            # Get available interfaces for DAG planning
            available_interfaces = interface_library.get_descriptions()
            
            # Generate DAG plan
            dag = dag_planner.generate_dag(query, available_interfaces)
            total_tokens += dag.get("token_usage", {}).get("total_tokens", 0)
            
            if dag.get("use_dag"):
                logger.info("Using DAG execution with %d steps", len(dag.get("steps", [])))
                use_dag = True
                
                # Execute DAG
                dag_result = dag_executor.execute_dag(dag, query)
                
                if dag_result["success"]:
                    # Collect all chart paths from DAG execution
                    chart_paths = []
                    for step_result in dag_result["steps_results"].values():
                        if isinstance(step_result, dict):
                            for key, value in step_result.items():
                                if (key.endswith("_chart_path") or key.endswith("_path") or key == "chart_path") and isinstance(value, str):
                                    chart_paths.append(value)
                    
                    chart_path = chart_paths[0] if chart_paths else None
                    
                    # Synthesize answer
                    answer, synth_tokens = self.agent.synthesize_answer(
                        query,
                        f"DAG ({dag_result['steps_executed']} steps)",
                        {},
                        dag_result["result"],
                        is_new=bool(dag_result["interfaces_created"])
                    )
                    total_tokens += synth_tokens.get("total_tokens", 0)
                    
                    if dag_result["interfaces_created"]:
                        interfaces_list = ", ".join(f"`{name}`" for name in dag_result["interfaces_created"])
                        answer = f"✨ *Multi-step execution: {dag_result['steps_executed']} steps, created interfaces: {interfaces_list}*\n\n{answer}"
                    
                    latency_ms = (time.perf_counter() - start) * 1000
                    logger.info("DAG execution complete | steps=%d | new_interfaces=%d | latency=%.0fms | tokens=%d",
                                dag_result['steps_executed'], len(dag_result['interfaces_created']), latency_ms, total_tokens)
                    
                    return {
                        "answer": answer,
                        "tool_used": "DAG Multi-Step",
                        "tool_args": {"steps": len(dag["steps"])},
                        "args_from_history": [],
                        "chart_path": chart_path,
                        "chart_paths": chart_paths,
                        "routing_mode": routing_mode or settings.routing_mode,
                        "latency_ms": latency_ms,
                        "is_new_interface": bool(dag_result["interfaces_created"]),
                        "token_usage": total_tokens,
                        "used_dag": True,
                        "dag_steps": dag_result['steps_executed'],
                    }
                else:
                    logger.warning("DAG execution failed: %s - falling back to single-step", dag_result["error"])
                    # Fall through to single-step execution
            else:
                logger.info("DAG planner determined single-step is sufficient: %s", dag.get("reason", ""))

        # ── Single-Step Execution (original logic) ──────────────
        candidate = self.retriever.best_match(query, threshold=0.20)  # Lowered from 0.25 to catch more candidates
        candidate_score = None
        if candidate:
            # Get the actual similarity score for the LLM to reason about
            results = self.retriever.retrieve(query, top_k=1)
            if results:
                candidate_score = results[0]["score"]
        
        logger.info("Best match for query: %s (score=%.2f, threshold=0.20)",
                    candidate["name"] if candidate else "None",
                    candidate_score if candidate_score else 0.0)

        # ── Step 2: LLM decides reuse or create ───────────────
        decision = self.agent.decide(query, candidate, candidate_score, history=history)
        action = decision.get("action", "create")
        interface_name = decision.get("interface_name")
        args = decision.get("args") or {}
        
        # Track tokens from decision
        total_tokens += decision.get("token_usage", {}).get("total_tokens", 0)

        logger.info("Decision: action=%s | interface=%s | args=%s",
                    action, interface_name, args)

        # ── Step 3: Create new interface if needed ─────────────
        if action == "create":
            logger.info("Creating new interface for query: %s", query)
            gen = self.agent.generate_interface(query)
            
            # Track tokens from generation
            total_tokens += gen.get("token_usage", {}).get("total_tokens", 0)

            if not gen["success"]:
                latency_ms = (time.perf_counter() - start) * 1000
                return {
                    "answer": f"⚠️ Could not generate a working interface: {gen['error']}",
                    "tool_used": None, "tool_args": None,
                    "args_from_history": [],
                    "chart_path": None,
                    "routing_mode": routing_mode or settings.routing_mode,
                    "latency_ms": latency_ms,
                    "is_new_interface": False,
                    "token_usage": total_tokens,
                }

            # Add to library and rebuild index
            interface_library.add(
                name=gen["name"],
                code=gen["code"],
                description=gen["description"],
                test_query=query,
            )
            self._rebuild_index()
            interface_name = gen["name"]
            args = gen["args"]
            is_new_interface = True
            logger.info("New interface added: %s", interface_name)

        # ── Step 4: Execute ────────────────────────────────────
        exec_result = self.executor.execute(interface_name, args)
        tool_output = exec_result.get("result") or {}
        error = exec_result.get("error")

        # ── Step 4b: FALLBACK - If execution failed, create new interface ───
        if error and not is_new_interface:
            logger.warning("Interface '%s' execution failed: %s. Creating new interface as fallback.",
                          interface_name, error)
            gen = self.agent.generate_interface(query)
            
            # Track tokens from fallback generation
            total_tokens += gen.get("token_usage", {}).get("total_tokens", 0)
            
            if gen["success"]:
                # Add to library and rebuild index
                interface_library.add(
                    name=gen["name"],
                    code=gen["code"],
                    description=gen["description"],
                    test_query=query,
                )
                self._rebuild_index()
                interface_name = gen["name"]
                args = gen["args"]
                is_new_interface = True
                logger.info("Fallback: New interface added: %s", interface_name)
                
                # Retry execution with new interface
                exec_result = self.executor.execute(interface_name, args)
                tool_output = exec_result.get("result") or {}
                error = exec_result.get("error")

        chart_path = None
        chart_paths = []
        if isinstance(tool_output, dict):
            # Collect all chart paths from the result
            for key, value in tool_output.items():
                if (key.endswith("_chart_path") or key.endswith("_path") or key == "chart_path") and isinstance(value, str):
                    chart_paths.append(value)
            
            # For backward compatibility, set chart_path to first one
            if chart_paths:
                chart_path = chart_paths[0]

        # ── Step 5: Synthesize answer ──────────────────────────
        if error:
            answer = f"⚠️ Execution error: {error}"
        else:
            answer, synth_tokens = self.agent.synthesize_answer(
                query, interface_name, args, tool_output, is_new=is_new_interface
            )
            total_tokens += synth_tokens.get("total_tokens", 0)
            if is_new_interface:
                answer = f"✨ *New interface created: `{interface_name}`*\n\n{answer}"

        # ── Detect params from history ─────────────────────────
        args_from_history: list[str] = []
        if args and history:
            query_lower = query.lower()
            for k, v in args.items():
                check = str(v).lower().replace(".ns", "").replace("_", " ")
                if check not in query_lower and str(v).lower() not in query_lower:
                    args_from_history.append(k)

        latency_ms = (time.perf_counter() - start) * 1000
        logger.info("Query done | interface=%s | new=%s | latency=%.0fms | tokens=%d",
                    interface_name, is_new_interface, latency_ms, total_tokens)

        return {
            "answer": answer,
            "tool_used": interface_name,
            "tool_args": args,
            "args_from_history": args_from_history,
            "chart_path": chart_path,
            "chart_paths": chart_paths,  # All chart paths
            "routing_mode": routing_mode or settings.routing_mode,
            "latency_ms": latency_ms,
            "is_new_interface": is_new_interface,
            "token_usage": total_tokens,
            "used_dag": False,
            "dag_steps": 0,
        }


agent_service = AgentService()
