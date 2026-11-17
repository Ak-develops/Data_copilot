#!/usr/bin/env python
"""Test a follow-up query to verify interface reuse from history."""

import requests
import json

# First query
query1 = "What was the latest closing price of TCS?"
print(f"Query 1: {query1}")
resp1 = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query1, 'routing_mode': 'vector', 'history': None},
    timeout=120
)
data1 = resp1.json()
print(f"  Tool used: {data1['tool_used']}")
print(f"  Is new: {data1['is_new_interface']}")
print()

# Build history from first query
history = [
    {"role": "user", "content": query1},
    {"role": "assistant", "content": data1['answer']}
]

# Follow-up query (should reuse the same interface, just with different ticker)
query2 = "What about Reliance?"
print(f"Query 2 (follow-up): {query2}")
resp2 = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query2, 'routing_mode': 'vector', 'history': history},
    timeout=120
)
data2 = resp2.json()
print(f"  Tool used: {data2['tool_used']}")
print(f"  Tool args: {data2['tool_args']}")
print(f"  Args from history: {data2['args_from_history']}")
print(f"  Is new: {data2['is_new_interface']}")
print()
print("Answer:")
print(data2['answer'])
