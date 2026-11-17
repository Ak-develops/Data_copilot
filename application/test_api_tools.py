#!/usr/bin/env python
"""Test what /api/tools returns by calling agent_service directly."""

from services.agent_service import agent_service
import json

print("=== Calling agent_service.list_tools() ===")
tools = agent_service.list_tools()
print(f"Result: {len(tools)} tools")
for t in tools:
    print(f"  - {t['name']}")

print("\n=== Calling interface_library.list_all() directly ===")
from model.tools import interface_library
all_ifaces = interface_library.list_all()
print(f"Result: {len(all_ifaces)} interfaces")
for i in all_ifaces:
    print(f"  - {i['name']}")
