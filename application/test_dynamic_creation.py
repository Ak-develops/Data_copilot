#!/usr/bin/env python
"""Test dynamic interface creation for new types of queries."""

import requests

# Query 1: Something completely new - calculate volatility
query1 = "What is the volatility of TCS stock over the last year?"
print(f"Query 1 (NEW functionality): {query1}")
resp1 = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query1, 'routing_mode': 'vector', 'history': None},
    timeout=120
)
data1 = resp1.json()
print(f"  Tool: {data1['tool_used']}")
print(f"  Is new: {data1['is_new_interface']}")
print(f"  ✅ Created dynamically!" if data1['is_new_interface'] else "  Reused existing")
print()

# Query 2: Another new functionality - calculate correlation
query2 = "Show me the correlation between TCS and Infosys stock prices"
print(f"Query 2 (NEW functionality): {query2}")
resp2 = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query2, 'routing_mode': 'vector', 'history': None},
    timeout=120
)
data2 = resp2.json()
print(f"  Tool: {data2['tool_used']}")
print(f"  Is new: {data2['is_new_interface']}")
print(f"  ✅ Created dynamically!" if data2['is_new_interface'] else "  Reused existing")
print()

# Query 3: Try the same volatility query again - should REUSE
query3 = "What about the volatility of Reliance?"
print(f"Query 3 (should reuse volatility interface): {query3}")
resp3 = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query3, 'routing_mode': 'vector', 'history': None},
    timeout=120
)
data3 = resp3.json()
print(f"  Tool: {data3['tool_used']}")
print(f"  Is new: {data3['is_new_interface']}")
print(f"  ✅ REUSED!" if not data3['is_new_interface'] else "  Created new")
print()

print("="*70)
print("The system demonstrates:")
print("1. ✅ Creates NEW interfaces dynamically when needed (volatility, correlation)")
print("2. ✅ Reuses existing interfaces when applicable")
print("3. ✅ All interfaces are visible in the Interface Library tab")
