try:
    from langchain.agents import AgentExecutor
    print("AgentExecutor found in langchain.agents")
except Exception as e:
    print(f"AgentExecutor NOT in langchain.agents: {e}")

try:
    from langchain_core.agents import AgentExecutor
    print("AgentExecutor found in langchain_core.agents")
except Exception as e:
    print(f"AgentExecutor NOT in langchain_core.agents: {e}")

try:
    from langgraph.prebuilt import create_react_agent
    print("create_react_agent found in langgraph.prebuilt")
except Exception as e:
    print(f"create_react_agent NOT in langgraph.prebuilt: {e}")

try:
    from langchain.agents import create_react_agent
    print("create_react_agent found in langchain.agents")
except Exception as e:
    print(f"create_react_agent NOT in langchain.agents: {e}")

try:
    from langgraph.prebuilt.chat_agent_executor import create_react_agent
    print("create_react_agent found in langgraph.prebuilt.chat_agent_executor")
except Exception as e:
    print(f"create_react_agent NOT in langgraph.prebuilt.chat_agent_executor: {e}")
