"""DAG Executor - Executes multi-step workflows with dependency resolution."""

from __future__ import annotations

import time
from typing import Any
from collections import defaultdict

from logger import get_logger, sanitize_args, truncate_payload
from model.executor import Executor
from model.agent import Agent
from model.tools import interface_library

logger = get_logger(__name__)


class DAGExecutor:
    """Executes multi-step DAGs with dependency resolution and parallel execution."""

    def __init__(self) -> None:
        self.executor = Executor()
        self.agent = Agent()

    def execute_dag(self, dag: dict[str, Any], query: str) -> dict[str, Any]:
        """
        Execute a multi-step DAG.
        
        Returns:
            {
              "success": bool,
              "result": dict,  # Final step result
              "steps_executed": int,
              "steps_results": dict,  # All intermediate results
              "error": str | None,
              "interfaces_created": list[str],
            }
        """
        steps = dag["steps"]
        results = {}  # step_id -> result
        interfaces_created = []
        
        # Sort steps by dependencies (topological sort)
        try:
            sorted_steps = self._topological_sort(steps)
        except ValueError as e:
            return {
                "success": False,
                "result": None,
                "steps_executed": 0,
                "steps_results": {},
                "error": f"DAG sorting failed: {e}",
                "interfaces_created": [],
            }
        
        logger.info("Executing DAG with %d steps", len(sorted_steps))
        dag_start = time.perf_counter()

        for step in sorted_steps:
            step_id = step["id"]
            interface_name = step["interface"]
            args = step.get("args", {})
            description = step.get("description", "")
            step_start = time.perf_counter()

            logger.info("DAG step %d start | interface=%s | desc=%s", step_id, interface_name, truncate_payload(description, 200))

            try:
                # Resolve argument references ($step1.result)
                resolved_args = self._resolve_references(args, results)
                logger.debug("DAG step %d resolved args: %s", step_id, sanitize_args(resolved_args))
            except Exception as e:
                step_ms = (time.perf_counter() - step_start) * 1000
                logger.error("DAG step %d failed arg resolution (duration=%.1fms): %s", step_id, step_ms, e)
                return {
                    "success": False,
                    "result": None,
                    "steps_executed": step_id - 1,
                    "steps_results": results,
                    "error": f"Step {step_id} arg resolution failed: {e}",
                    "interfaces_created": interfaces_created,
                }
            
            # Check if interface needs to be created
            if interface_name == "CREATE_NEW" or not interface_library.has(interface_name):
                logger.info("Creating new interface for step %d", step_id)
                
                # Build focused query for interface generation
                gen_query = description
                if resolved_args:
                    # Show example args to help interface generation
                    arg_sample = {k: v for k, v in list(resolved_args.items())[:3]}
                    gen_query = f"{description} (example args: {arg_sample})"
                
                gen_result = self.agent.generate_interface(gen_query)
                
                if not gen_result["success"]:
                    step_ms = (time.perf_counter() - step_start) * 1000
                    error_msg = gen_result.get('error', 'Unknown error')[:200]
                    logger.error("DAG step %d failed interface creation (duration=%.1fms): %s", step_id, step_ms, error_msg)
                    return {
                        "success": False,
                        "result": None,
                        "steps_executed": step_id - 1,
                        "steps_results": results,
                        "error": f"Step {step_id} interface creation failed: {error_msg}",
                        "interfaces_created": interfaces_created,
                    }
                
                # Add to library
                interface_library.add(
                    name=gen_result["name"],
                    code=gen_result["code"],
                    description=gen_result["description"],
                    test_query=gen_query,
                )
                
                interface_name = gen_result["name"]
                interfaces_created.append(interface_name)
                logger.info("Created interface '%s' for step %d", interface_name, step_id)
                
                # Use generated args if none provided or resolved
                if not resolved_args:
                    resolved_args = gen_result["args"]
            
            # Execute step
            exec_result = self.executor.execute(interface_name, resolved_args)
            step_ms = (time.perf_counter() - step_start) * 1000
            
            if exec_result.get("error"):
                error_msg = exec_result['error'][:200]
                logger.error("DAG step %d failed | interface=%s | status=failure | duration=%.1fms | error=%s",
                             step_id, interface_name, step_ms, error_msg)
                return {
                    "success": False,
                    "result": None,
                    "steps_executed": step_id,
                    "steps_results": results,
                    "error": f"Step {step_id} ({interface_name}) failed: {error_msg}",
                    "interfaces_created": interfaces_created,
                }
            
            # Store result
            result_data = exec_result.get("result", {})
            results[step_id] = result_data
            logger.info("DAG step %d completed | interface=%s | status=success | duration=%.1fms",
                        step_id, interface_name, step_ms)
            logger.debug("DAG step %d output: %s", step_id, truncate_payload(result_data, 500))
        
        # Return final step result
        final_step_id = sorted_steps[-1]["id"]
        final_result = results.get(final_step_id, {})
        total_dag_ms = (time.perf_counter() - dag_start) * 1000

        logger.info("DAG execution complete | steps=%d | interfaces_created=%d | duration=%.1fms", 
                    len(sorted_steps), len(interfaces_created), total_dag_ms)
        
        return {
            "success": True,
            "result": final_result,
            "steps_executed": len(sorted_steps),
            "steps_results": results,
            "error": None,
            "interfaces_created": interfaces_created,
        }

    def _topological_sort(self, steps: list[dict]) -> list[dict]:
        """Sort steps by dependencies using topological sort."""
        # Build adjacency list
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        step_map = {step["id"]: step for step in steps}
        
        for step in steps:
            step_id = step["id"]
            in_degree[step_id] = len(step["depends_on"])
            for dep_id in step["depends_on"]:
                graph[dep_id].append(step_id)
        
        # Kahn's algorithm
        queue = [sid for sid in step_map if in_degree[sid] == 0]
        sorted_steps = []
        
        while queue:
            # Sort queue to ensure deterministic execution order
            queue.sort()
            step_id = queue.pop(0)
            sorted_steps.append(step_map[step_id])
            
            for neighbor in graph[step_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(sorted_steps) != len(steps):
            raise ValueError("Circular dependency detected in DAG")
        
        return sorted_steps

    def _resolve_references(self, args: dict, results: dict[int, Any]) -> dict:
        """Resolve $stepX.result references in arguments."""
        resolved = {}
        
        for key, value in args.items():
            if isinstance(value, str) and value.startswith("$step"):
                # Parse reference: $step1.result or $step1.result.ticker
                match = value.replace("$step", "").split(".", 1)
                step_id = int(match[0])
                
                if step_id not in results:
                    raise ValueError(f"Step {step_id} result not available for reference")
                
                # Get result
                result = results[step_id]
                
                # Navigate path if specified (e.g., result.ticker)
                if len(match) > 1 and match[1] != "result":
                    path_parts = match[1].replace("result.", "").split(".")
                    for part in path_parts:
                        if isinstance(result, dict):
                            result = result.get(part)
                        else:
                            raise ValueError(f"Cannot navigate path {match[1]} in step {step_id} result")
                
                resolved[key] = result
            else:
                resolved[key] = value
        
        return resolved


# Singleton
dag_executor = DAGExecutor()
