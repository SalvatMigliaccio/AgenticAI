#!/usr/bin/env python
"""Test what's available in LangChain for agent creation."""

import sys

# Test AgentExecutor locations
locations = [
    ("langchain.experimental.agents", "AgentExecutor"),
    ("langchain_experimental.agents", "AgentExecutor"),
    ("langchain.schema", "AgentAction"),
]

print("LangChain Agent Components Search:")
print("=" * 50)

for module_path, name in locations:
    try:
        module = __import__(module_path, fromlist=[name])
        if hasattr(module, name):
            print(f"✓ {name} found in {module_path}")
        else:
            print(f"✗ {name} NOT in {module_path}")
    except ImportError:
        print(f"✗ {module_path} not available")

# List what create_agent returns
print("\nTesting create_agent function:")
print("=" * 50)
try:
    from langchain.agents import create_agent
    print("✓ create_agent imported successfully")
    print(f"  create_agent: {create_agent}")
    print(f"  create_agent.__doc__: {create_agent.__doc__[:200] if create_agent.__doc__ else 'No docstring'}")
except Exception as e:
    print(f"✗ Error: {e}")
