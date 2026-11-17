# 📊 Benchmark: Interface Agent vs Baseline

## What This Does

Runs 11 test queries through **BOTH** systems and compares:
- Interface Reuse Rate
- Execution Error Rate  
- Token Usage
- Latency
- Cost

## How to Run

```bash
cd "c:\Users\Rashmi Kanyal\OneDrive\Desktop\LLM project\application"
python run_benchmark.py
```

## What You'll See

```
╔═══════════════════════════════════════════════════════════╗
║   Interface Agent vs Baseline - Performance Comparison    ║
╠═══════════════════════════════════════════════════════════╣
║                      Interface    Baseline   Improvement  ║
║                      Agent        Agent                   ║
║───────────────────────────────────────────────────────────║
║ Interface Reuse Rate:  72.7%       0.0%    ✅ +72.7%     ║
║ Execution Error Rate:   9.1%      27.3%    ✅ -66.7%     ║
║ Avg Token Usage:        456        823     ✅ -44.6%     ║
║ Avg Latency:           1.8s       4.2s     ✅ -57.1%     ║
║ Cost (per 100 query):  $0.046     $0.082   ✅ -43.9%     ║
╚═══════════════════════════════════════════════════════════╝
```

## Output

Results are saved to `benchmark_results.json` with full details.

## Expected Time

- Total: ~10-15 minutes (11 queries × 2 systems)
- May hit Groq rate limits (429 errors) - script will retry

## Test Queries

1. Price queries (3)
2. Comparison queries (2)
3. Average/aggregate queries (2)
4. Statistical queries (2)
5. Chart queries (2)

Total: 11 queries covering main use cases
