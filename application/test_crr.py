#!/usr/bin/env python
"""Test Code Reuse Rate (CRR) with follow-up queries that inherit parameters."""

import requests

API_BASE = "http://localhost:8000"

print("="*70)
print("Testing Code Reuse Rate (CRR) - Parameter Inheritance")
print("="*70)
print()

# Query 1: Initial query with explicit parameters
query1 = "What is the latest closing price of TCS?"
print(f"Query 1: {query1}")
resp1 = requests.post(
    f"{API_BASE}/api/chat",
    json={'query': query1, 'routing_mode': 'vector', 'history': None},
    timeout=120
)
data1 = resp1.json()
print(f"  Interface: {data1['tool_used']}")
print(f"  Args: {data1['tool_args']}")
print(f"  Args from history: {data1['args_from_history']}")
print(f"  CRR: {len(data1['args_from_history']) / len(data1['tool_args']) * 100 if data1['tool_args'] else 0:.0f}%")
print()

# Build conversation history
history = [
    {"role": "user", "content": query1},
    {"role": "assistant", "content": data1['answer']}
]

# Query 2: Follow-up WITHOUT mentioning the ticker - should inherit TCS
query2 = "What about the volatility?"
print(f"Query 2 (follow-up): {query2}")
print(f"  (Should inherit ticker 'TCS' from Query 1)")
resp2 = requests.post(
    f"{API_BASE}/api/chat",
    json={'query': query2, 'routing_mode': 'vector', 'history': history},
    timeout=120
)
data2 = resp2.json()
print(f"  Interface: {data2['tool_used']}")
print(f"  Args: {data2['tool_args']}")
print(f"  Args from history: {data2['args_from_history']}")
print(f"  CRR: {len(data2['args_from_history']) / len(data2['tool_args']) * 100 if data2['tool_args'] else 0:.0f}%")
print()

# Update history
history.extend([
    {"role": "user", "content": query2},
    {"role": "assistant", "content": data2['answer']}
])

# Query 3: Another follow-up with explicit new parameter
query3 = "Now show me the latest price of Reliance"
print(f"Query 3 (new ticker): {query3}")
resp3 = requests.post(
    f"{API_BASE}/api/chat",
    json={'query': query3, 'routing_mode': 'vector', 'history': history},
    timeout=120
)
data3 = resp3.json()
print(f"  Interface: {data3['tool_used']}")
print(f"  Args: {data3['tool_args']}")
print(f"  Args from history: {data3['args_from_history']}")
print(f"  CRR: {len(data3['args_from_history']) / len(data3['tool_args']) * 100 if data3['tool_args'] else 0:.0f}%")
print()

# Update history
history.extend([
    {"role": "user", "content": query3},
    {"role": "assistant", "content": data3['answer']}
])

# Query 4: Follow-up that should inherit Reliance
query4 = "What's the volatility for this one?"
print(f"Query 4 (follow-up): {query4}")
print(f"  (Should inherit ticker 'Reliance' from Query 3)")
resp4 = requests.post(
    f"{API_BASE}/api/chat",
    json={'query': query4, 'routing_mode': 'vector', 'history': history},
    timeout=120
)
data4 = resp4.json()
print(f"  Interface: {data4['tool_used']}")
print(f"  Args: {data4['tool_args']}")
print(f"  Args from history: {data4['args_from_history']}")
print(f"  CRR: {len(data4['args_from_history']) / len(data4['tool_args']) * 100 if data4['tool_args'] else 0:.0f}%")
print()

print("="*70)
print("Expected CRR Pattern:")
print("  Query 1: CRR = 0% (initial query, all params explicit)")
print("  Query 2: CRR > 0% (inherits 'ticker' from Query 1)")
print("  Query 3: CRR = 0% (new ticker explicitly mentioned)")
print("  Query 4: CRR > 0% (inherits 'ticker' from Query 3)")
print("="*70)
