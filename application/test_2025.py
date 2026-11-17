#!/usr/bin/env python
"""Test query for year 2025 (outside available data range)."""

import requests

query = "give me a graph showing the value of the stock of these 2 companies tcs and wipro for the year 2025"
print(f"Query: {query}")
print("(Note: Data is only available for 2022-2024)")
print()

resp = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query, 'routing_mode': 'vector', 'history': None},
    timeout=120
)

if resp.ok:
    data = resp.json()
    print(f"Tool: {data['tool_used']}")
    print(f"Latency: {data['latency_ms']:.0f}ms")
    print()
    print("Answer:")
    print(data['answer'])
    if data.get('chart_path'):
        print(f"\nChart saved to: {data['chart_path']}")
else:
    print(f"Error: {resp.status_code}")
    print(resp.text)
