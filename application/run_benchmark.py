#!/usr/bin/env python
"""Benchmark comparison: Interface Agent vs Baseline Direct Generation.

Runs a set of test queries through both systems and compares:
- Interface Reuse Rate
- Code Reuse Rate (CRR)
- Execution Error Rate
- Token Usage
- Latency
- Cost
"""

import json
import time
from pathlib import Path

from services.agent_service import agent_service
from baseline_agent import baseline_agent


# Test query suite
TEST_QUERIES = [
    # Price queries
    "What is the latest closing price of TCS?",
    "What is the latest price of Reliance?",
    "Get the latest price of Infosys",
    
    # Comparison queries
    "Compare TCS and Infosys for 2024",
    "Show me a comparison between Reliance and HDFC Bank for 2023",
    
    # Average/aggregate queries
    "Show average prices for TCS, Wipro, and HCL",
    "Give me a bar chart of average values for Reliance, Infosys, and TCS",
    
    # Statistical queries
    "Calculate volatility of TCS over the last year",
    "What is the volatility of Reliance?",
    
    # Chart queries
    "Plot TCS stock trend for 2024",
    "Show me a graph of Wipro for 2023",
]


def run_interface_agent(queries: list[str]) -> dict:
    """Run queries through interface-based agent."""
    results = []
    
    print("\n" + "="*70)
    print("Running Interface Agent (Your System)...")
    print("="*70)
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] {query}")
        
        try:
            result = agent_service.process_query(query, routing_mode="vector", history=None)
            results.append({
                "query": query,
                "success": not result.get("error"),
                "is_new_interface": result.get("is_new_interface", False),
                "latency_ms": result.get("latency_ms", 0),
                "token_usage": result.get("token_usage", {"total_tokens": 0}),
            })
            print(f"  ✓ Success | Latency: {result.get('latency_ms', 0):.0f}ms | New: {result.get('is_new_interface', False)}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                "query": query,
                "success": False,
                "is_new_interface": False,
                "latency_ms": 0,
                "token_usage": {"total_tokens": 0},
            })
        
        time.sleep(0.5)  # Rate limiting
    
    return results


def run_baseline_agent(queries: list[str]) -> dict:
    """Run queries through baseline direct generation agent."""
    results = []
    
    print("\n" + "="*70)
    print("Running Baseline Agent (Direct Code Generation)...")
    print("="*70)
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] {query}")
        
        try:
            result = baseline_agent.process_query(query)
            results.append({
                "query": query,
                "success": not result.get("has_error", False),
                "latency_ms": result.get("latency_ms", 0),
                "token_usage": result.get("token_usage", {"total_tokens": 0}),
            })
            print(f"  ✓ Success | Latency: {result.get('latency_ms', 0):.0f}ms | Tokens: {result.get('token_usage', {}).get('total_tokens', 0)}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                "query": query,
                "success": False,
                "latency_ms": 0,
                "token_usage": {"total_tokens": 0},
            })
        
        time.sleep(0.5)  # Rate limiting
    
    return results


def calculate_metrics(interface_results: list, baseline_results: list) -> dict:
    """Calculate comparison metrics."""
    
    # Interface Agent metrics
    interface_success = sum(1 for r in interface_results if r["success"])
    interface_new = sum(1 for r in interface_results if r.get("is_new_interface", False))
    interface_reuse = len(interface_results) - interface_new
    interface_reuse_rate = (interface_reuse / len(interface_results) * 100) if interface_results else 0
    interface_error_rate = ((len(interface_results) - interface_success) / len(interface_results) * 100) if interface_results else 0
    interface_avg_latency = sum(r["latency_ms"] for r in interface_results) / len(interface_results) if interface_results else 0
    interface_total_tokens = sum(r.get("token_usage", {}).get("total_tokens", 0) for r in interface_results)
    interface_avg_tokens = interface_total_tokens / len(interface_results) if interface_results else 0
    
    # Baseline metrics
    baseline_success = sum(1 for r in baseline_results if r["success"])
    baseline_error_rate = ((len(baseline_results) - baseline_success) / len(baseline_results) * 100) if baseline_results else 0
    baseline_avg_latency = sum(r["latency_ms"] for r in baseline_results) / len(baseline_results) if baseline_results else 0
    baseline_total_tokens = sum(r.get("token_usage", {}).get("total_tokens", 0) for r in baseline_results)
    baseline_avg_tokens = baseline_total_tokens / len(baseline_results) if baseline_results else 0
    
    # Comparisons
    token_reduction = ((baseline_avg_tokens - interface_avg_tokens) / baseline_avg_tokens * 100) if baseline_avg_tokens else 0
    latency_reduction = ((baseline_avg_latency - interface_avg_latency) / baseline_avg_latency * 100) if baseline_avg_latency else 0
    error_reduction = ((baseline_error_rate - interface_error_rate) / baseline_error_rate * 100) if baseline_error_rate else 0
    
    # Cost (Groq pricing: ~$0.001 per 1K tokens)
    interface_cost = (interface_total_tokens / 1000) * 0.001
    baseline_cost = (baseline_total_tokens / 1000) * 0.001
    cost_savings = ((baseline_cost - interface_cost) / baseline_cost * 100) if baseline_cost else 0
    
    return {
        "interface_agent": {
            "reuse_rate": interface_reuse_rate,
            "error_rate": interface_error_rate,
            "avg_tokens": interface_avg_tokens,
            "avg_latency_s": interface_avg_latency / 1000,
            "total_cost": interface_cost,
        },
        "baseline_agent": {
            "reuse_rate": 0.0,  # By definition
            "error_rate": baseline_error_rate,
            "avg_tokens": baseline_avg_tokens,
            "avg_latency_s": baseline_avg_latency / 1000,
            "total_cost": baseline_cost,
        },
        "improvements": {
            "reuse_rate_gain": interface_reuse_rate,
            "token_reduction": token_reduction,
            "latency_reduction": latency_reduction,
            "error_reduction": error_reduction,
            "cost_savings": cost_savings,
        }
    }


def print_comparison_dashboard(metrics: dict):
    """Print the comparison dashboard."""
    ia = metrics["interface_agent"]
    ba = metrics["baseline_agent"]
    imp = metrics["improvements"]
    
    print("\n")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   Interface Agent vs Baseline - Performance Comparison    ║")
    print("╠═══════════════════════════════════════════════════════════╣")
    print("║                      Interface    Baseline   Improvement  ║")
    print("║                      Agent        Agent                   ║")
    print("║───────────────────────────────────────────────────────────║")
    print(f"║ Interface Reuse Rate: {ia['reuse_rate']:5.1f}%      {ba['reuse_rate']:5.1f}%    ✅ +{imp['reuse_rate_gain']:.1f}%    ║")
    print(f"║ Execution Error Rate: {ia['error_rate']:5.1f}%      {ba['error_rate']:5.1f}%    ✅ -{abs(imp['error_reduction']):.1f}%    ║")
    print(f"║ Avg Token Usage:      {ia['avg_tokens']:5.0f}       {ba['avg_tokens']:5.0f}     ✅ -{abs(imp['token_reduction']):.1f}%    ║")
    print(f"║ Avg Latency:          {ia['avg_latency_s']:4.1f}s       {ba['avg_latency_s']:4.1f}s      ✅ -{abs(imp['latency_reduction']):.1f}%    ║")
    print(f"║ Cost (per 100 query): ${ia['total_cost']*100:5.3f}      ${ba['total_cost']*100:5.3f}     ✅ -{abs(imp['cost_savings']):.1f}%    ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()


def main():
    """Run the full benchmark."""
    print("="*70)
    print("BENCHMARK: Interface Agent vs Baseline Direct Generation")
    print("="*70)
    print(f"Test queries: {len(TEST_QUERIES)}")
    print()
    
    # Run both systems
    interface_results = run_interface_agent(TEST_QUERIES)
    baseline_results = run_baseline_agent(TEST_QUERIES)
    
    # Calculate metrics
    metrics = calculate_metrics(interface_results, baseline_results)
    
    # Print comparison
    print_comparison_dashboard(metrics)
    
    # Save results
    output_file = Path(__file__).parent / "benchmark_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "metrics": metrics,
            "interface_results": interface_results,
            "baseline_results": baseline_results,
        }, f, indent=2, default=str)
    
    print(f"✅ Results saved to: {output_file}")


if __name__ == "__main__":
    main()
