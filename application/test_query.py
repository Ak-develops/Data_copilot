#!/usr/bin/env python
"""Test a simple query to verify the full pipeline works."""

import requests
import json

query = "What was the latest closing price of TCS?"
print(f"Sending query: {query}")
print()

resp = requests.post(
    'http://localhost:8000/api/chat',
    json={
        'query': query,
        'routing_mode': 'vector',
        'history': None
    },
    timeout=120
)

if resp.ok:
    data = resp.json()
    print("✅ Query succeeded!")
    print()
    print(f"Tool used: {data['tool_used']}")
    print(f"Is new interface: {data['is_new_interface']}")
    print(f"Latency: {data['latency_ms']:.0f}ms")
    print()
    print("Answer:")
    print(data['answer'])
    print()
    print(f"Tool args: {data['tool_args']}")
else:
    print(f"❌ Query failed: {resp.status_code}")
    print(resp.text)
