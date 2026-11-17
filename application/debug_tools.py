#!/usr/bin/env python
"""Debug script to check agent_service.list_tools() output."""

from services.agent_service import agent_service
import json

tools = agent_service.list_tools()
print(f"agent_service.list_tools() returns {len(tools)} tools:")
print(json.dumps(tools, indent=2))

print("\n\n=== Also check InterfaceLibrary directly ===")
from model.tools import interface_library
all_interfaces = interface_library.list_all()
print(f"interface_library.list_all() returns {len(all_interfaces)} interfaces:")
for iface in all_interfaces:
    print(f"  - {iface['name']}")
