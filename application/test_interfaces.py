#!/usr/bin/env python
"""Quick test to check the interface library state."""

from model.tools import interface_library
import json

all_interfaces = interface_library.list_all()
print(f'Total interfaces in library: {len(all_interfaces)}')
for iface in all_interfaces:
    print(f'  - {iface["name"]}: {iface["description"][:60]}')
