#!/usr/bin/env python
"""Test if the system reuses interfaces more intelligently."""

import requests

# Query 1: Should match existing "plot_average_stock_values" or similar
query1 = "Show me the average stock prices for TCS, Reliance, and Infosys"
print(f"Query 1: {query1}")
resp1 = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query1, 'routing_mode': 'vector', 'history': None},
    timeout=120
)
data1 = resp1.json()
print(f"  Tool: {data1['tool_used']}")
print(f"  Is new: {data1['is_new_interface']}")
print()

# Query 2: Similar to Query 1, should REUSE
query2 = "Give me a graph showing average values for Wipro and HCL"
print(f"Query 2 (should reuse): {query2}")
resp2 = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query2, 'routing_mode': 'vector', 'history': None},
    timeout=120
)
data2 = resp2.json()
print(f"  Tool: {data2['tool_used']}")
print(f"  Is new: {data2['is_new_interface']}")
print(f"  ✅ REUSED!" if not data2['is_new_interface'] else "  ❌ Created new (should have reused)")
print()

print("="*60)
print("Check the Interface Library tab to see:")
print("1. All registered interfaces")
print("2. Which interfaces were used for each query")
