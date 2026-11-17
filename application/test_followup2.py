#!/usr/bin/env python
"""Test a more explicit follow-up query that should reuse the existing interface."""

import requests

# First query
query1 = "What is the latest closing price of TCS?"
print(f"Query 1: {query1}")
resp1 = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query1, 'routing_mode': 'vector', 'history': None},
    timeout=120
)
data1 = resp1.json()
print(f"  Tool: {data1['tool_used']}, New: {data1['is_new_interface']}")

# Build history
history = [
    {"role": "user", "content": query1},
    {"role": "assistant", "content": data1['answer']}
]

# Follow-up query - very explicit to trigger reuse
query2 = "Now what is the latest closing price of Reliance?"
print(f"\nQuery 2 (explicit follow-up): {query2}")
resp2 = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query2, 'routing_mode': 'vector', 'history': history},
    timeout=120
)
data2 = resp2.json()
print(f"  Tool: {data2['tool_used']}, New: {data2['is_new_interface']}")
print(f"  Tool args: {data2['tool_args']}")
print(f"  Args from history: {data2['args_from_history']}")
