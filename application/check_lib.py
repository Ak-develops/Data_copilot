#!/usr/bin/env python
"""Check current interface library."""

import requests

r = requests.get('http://localhost:8000/api/tools', timeout=10)
tools = r.json()
print(f'Total interfaces: {len(tools)}')
for t in tools:
    print(f'  - {t["name"]}')
