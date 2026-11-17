#!/usr/bin/env python
"""Test the reset functionality."""

import requests

API_BASE = "http://localhost:8000"

print("Testing Reset Functionality")
print("="*70)

# Check current interfaces
print("\n1. Checking current interfaces...")
resp = requests.get(f"{API_BASE}/api/tools", timeout=10)
interfaces = resp.json()
print(f"   Current interfaces: {len(interfaces)}")
for i in interfaces:
    print(f"     - {i['name']}")

# Create a new interface if empty
if len(interfaces) == 0:
    print("\n2. Creating a test interface...")
    resp = requests.post(
        f"{API_BASE}/api/chat",
        json={'query': 'What is the latest price of TCS?', 'routing_mode': 'vector'},
        timeout=120
    )
    print(f"   Query executed. Interface: {resp.json()['tool_used']}")
    
    # Check again
    resp = requests.get(f"{API_BASE}/api/tools", timeout=10)
    interfaces = resp.json()
    print(f"   Current interfaces: {len(interfaces)}")

# Test reset
print("\n3. Testing RESET...")
resp = requests.post(f"{API_BASE}/api/reset", timeout=10)
if resp.ok:
    print(f"   ✅ Reset successful: {resp.json()['message']}")
else:
    print(f"   ❌ Reset failed: {resp.text}")

# Verify reset
print("\n4. Verifying reset...")
resp = requests.get(f"{API_BASE}/api/tools", timeout=10)
interfaces = resp.json()
print(f"   Current interfaces: {len(interfaces)}")
if len(interfaces) == 0:
    print("   ✅ All interfaces cleared!")
else:
    print(f"   ❌ Still has {len(interfaces)} interfaces")
    for i in interfaces:
        print(f"     - {i['name']}")

print("\n" + "="*70)
print("Reset test complete!")
