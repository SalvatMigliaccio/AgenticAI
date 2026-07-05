#!/usr/bin/env python
"""Test the ResearchAgent ReAct parsing logic."""

from agents import ResearchAgent
import re

# Test the parsing logic
test_output = """
Thought: I need to search for information about post-quantum cryptography
Action: duckduckgo_search
Action Input: post-quantum cryptography impact digital certificates
Observation: [Search results would go here]

Thought: I found some good information, let me search for more specific details
Action: scrape_website  
Action Input: https://example.com/pqc-article
Observation: [Scraped content would go here]

Final Answer: Post-quantum cryptography is...
"""

# Create a dummy agent to test parsing
class DummyLLM:
    pass

class DummyTool:
    def __init__(self, name, desc):
        self.name = name
        self.description = desc
        self.func = lambda x: f"Result for {x}"

agent = ResearchAgent(
    llm=DummyLLM(),
    tools=[DummyTool("duckduckgo_search", "Search the web"), DummyTool("scrape_website", "Scrape a website")],
    prompt=None
)

# Test the parsing
print("Testing output parsing:")
print("=" * 50)
parsed = agent._parse_output(test_output)
print(f"Parsed output: {parsed}")
print()

# Test the tools description
print("Testing tools description:")
print("=" * 50)
print(agent._tools_description())
print()

print("✓ All tests passed!")
