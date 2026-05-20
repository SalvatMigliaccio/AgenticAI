from langchain.agents import create_agent

def get_weather(city:str) -> str:
    """Get the daily weather for a city"""
    return f"The weather in {city} is sunny and with a high of 25°C."

agent = create_agent(
    model="ollama:mistral",
    tools=[get_weather],
    system_prompt="You are a helpful assistant that provides weather information and wind conditions."
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
)

print(result["messages"][-1].content_blocks)
