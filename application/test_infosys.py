#!/usr/bin/env python
"""Test query with Infosys to verify ticker mapping fix."""

import requests

query = "What is the latest closing price of Infosys?"
print(f"Query: {query}")
print()

resp = requests.post(
    'http://localhost:8000/api/chat',
    json={'query': query, 'routing_mode': 'vector', 'history': None},
    timeout=120
)

if resp.ok:
    data = resp.json()
    print(f"Tool: {data['tool_used']}")
    print(f"Tool args: {data['tool_args']}")
    print(f"Is new: {data['is_new_interface']}")
    print()
    print("Answer:")
    print(data['answer'])
else:
    print(f"Error: {resp.status_code}")
    print(resp.text)
