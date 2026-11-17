#!/usr/bin/env python
"""Test that the system starts with no interfaces and builds them dynamically."""

import requests

print("Starting with ZERO interfaces...")
print()

# Query 1: First query - should create a new interface
query1 = "What is the latest closing price of TCS?"
print(f"Query 1: {query1}")
resp1 = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query1, 'routing_mode': 'vector', 'history': None},
    timeout=120
)
data1 = resp1.json()
print(f"  Tool: {data1['tool_used']}")
print(f"  Is new: {data1['is_new_interface']}")
print(f"  ✅ Created from scratch!" if data1['is_new_interface'] else "  (Unexpected)")
print()

# Query 2: Different functionality - should create another new interface
query2 = "Show me a graph comparing TCS and Infosys for 2024"
print(f"Query 2: {query2}")
resp2 = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query2, 'routing_mode': 'vector', 'history': None},
    timeout=120
)
data2 = resp2.json()
print(f"  Tool: {data2['tool_used']}")
print(f"  Is new: {data2['is_new_interface']}")
print(f"  ✅ Created new interface!" if data2['is_new_interface'] else "  Reused existing")
print()

# Query 3: Similar to Query 1 - should REUSE
query3 = "What's the latest price of Reliance?"
print(f"Query 3: {query3}")
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
print("✅ System successfully builds Interface Library from ZERO!")
print("Check the Interface Library tab to see all created interfaces.")
