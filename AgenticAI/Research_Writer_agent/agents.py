import os
import json
import re
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from tools import duckduckgo_tool, scrape_tool

load_dotenv()  # Load environment variables from .env file

# ---------------------------------------------------------------------------
# LLM — shared by both agents.
# In a real project you could give each agent a different model:
# researcher → faster model (llama3.2) for many tool calls
# writer     → more capable model (mistral-nemo) for long-form writing
# ---------------------------------------------------------------------------
def _make_llm(temperature: float = 0.0) -> ChatOllama:
    return ChatOllama(
        temperature=temperature,
        model=os.getenv("OLLAMA_MODEL", "mistral"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )
    
    
# ---------------------------------------------------------------------------
# Custom ReAct prompt for the Researcher
#
# Why a custom prompt instead of hub.pull("hwchase17/react")?
# We inject role, goal, and backstory directly into the system prompt
# so the agent behaves like a researcher, not a generic assistant.
# This is exactly what CrewAI does internally — we are just doing it
# explicitly so you can see how it works.
# ---------------------------------------------------------------------------
RESEARCHER_PROMPT = PromptTemplate.from_template(
    """
You are a Senior Research Analyst.
Your goal is to find accurate, comprehensive, and up-to-date information
about the given topic by searching the web and reading sources carefully.
You are methodical, skeptical of unverified claims, and always look for
multiple sources before drawing conclusions.

You have access to the following tools:
{tools}
Use this EXACT format for every reasoning step:

Thought: reason about what to do next
Action: the tool name (one of [{tool_names}])
Action Input: the input to the tool
Observation: the result of the tool call
... (repeat Thought/Action/Observation as many times as needed)
Thought: I now have enough information to write the research report
Final Answer: [your complete structured research report in markdown]

Rules:
- Always search at least 3 times with different queries before concluding
- Note the source URL for every important fact
- If a search result is too brief, scrape the full page for details
- Never invent facts — only report what you find

Begin!

Topic to research: {input}

{agent_scratchpad}
"""
)


# ---------------------------------------------------------------------------
# Custom prompt for the Writer
#
# The writer has NO tools — its prompt does not include a tool-calling
# loop. Instead it receives the research report as direct input and
# produces the article in a single pass.
# We use a simple PromptTemplate instead of a ReAct prompt because
# there is nothing to decide — just transform input into output.
# ---------------------------------------------------------------------------
WRITER_PROMPT = PromptTemplate.from_template("""
You are a Senior Content Writer with 10 years of experience turning
complex research into clear, engaging articles for a general audience.

You NEVER invent facts. You only write what the research report below supports.
You structure articles with a strong hook, logical flow with clear headings,
and a memorable conclusion.

Research report:
{research}

Topic: {topic}

Write a complete, publication-ready article in markdown format.
Requirements:
- Strong title as # heading
- Engaging introduction (hook the reader in the first paragraph)
- At least 3 body sections with ## headings
- Explain technical concepts with analogies where helpful
- Include specific facts and data from the research report
- A conclusion section that summarizes key takeaways
- Minimum 600 words
- Neutral, informative tone

Article:
""")



def build_researcher():
    """
    Build a ReAct agent executor for research. This creates a custom agent that:
    1. Uses the ReAct pattern (Reasoning + Acting)
    2. Calls search and scrape tools as needed
    3. Returns a dict-like executor that supports .invoke()
    """
    llm = _make_llm(temperature=0.0)  # deterministic
    tools = [duckduckgo_tool, scrape_tool]
    
    return ResearchAgent(llm=llm, tools=tools, prompt=RESEARCHER_PROMPT)


class ResearchAgent:
    """
    A custom ReAct agent executor for LangChain 1.3.1 compatibility.
    Implements the ReAct loop: Thought → Action → Observation → (repeat)
    """
    
    def __init__(self, llm, tools, prompt):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.prompt_template = prompt
        self.max_iterations = 10
        
    def invoke(self, inputs: dict) -> dict:
        """
        Main entry point for the agent.
        Takes {"input": topic} and returns {"output": research_report}
        """
        topic = inputs.get("input", "")
        scratchpad = ""
        
        for iteration in range(self.max_iterations):
            # Format the prompt with current state
            prompt_text = self.prompt_template.format(
                tools=self._tools_description(),
                tool_names=",".join(self.tools.keys()),
                input=topic,
                agent_scratchpad=scratchpad
            )
            
            # Call the LLM
            response = self.llm.invoke(prompt_text)
            output = response.content if hasattr(response, 'content') else str(response)
            
            # Check for Final Answer
            if "Final Answer:" in output:
                final_answer = output.split("Final Answer:")[-1].strip()
                return {"output": final_answer}
            
            # Parse and execute tool calls
            thought_action = self._parse_output(output)
            if not thought_action or "action" not in thought_action:
                # If we can't parse, assume we're done
                return {"output": output}
            
            action = thought_action["action"]
            action_input = thought_action["action_input"]
            
            # Execute the tool
            if action not in self.tools:
                observation = f"Error: unknown tool '{action}'"
            else:
                try:
                    observation = self.tools[action].func(action_input)
                except Exception as e:
                    observation = f"Error executing {action}: {str(e)}"
            
            # Update scratchpad
            scratchpad += f"\nThought: {thought_action.get('thought', '')}\n"
            scratchpad += f"Action: {action}\n"
            scratchpad += f"Action Input: {action_input}\n"
            scratchpad += f"Observation: {observation}\n"
        
        # Max iterations reached, return what we have
        return {"output": f"Research incomplete after {self.max_iterations} iterations.\n\n{scratchpad}"}
    
    def _parse_output(self, output: str) -> dict:
        """
        Parse LLM output to extract Thought, Action, and Action Input.
        Looks for patterns like:
            Thought: ...
            Action: tool_name
            Action Input: input_text
        """
        result = {}
        
        # Extract Thought
        thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|$)", output, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()
        
        # Extract Action
        action_match = re.search(r"Action:\s*(\w+)", output)
        if action_match:
            result["action"] = action_match.group(1).strip()
        
        # Extract Action Input
        action_input_match = re.search(r"Action Input:\s*(.+?)(?=\n|$)", output, re.DOTALL)
        if action_input_match:
            result["action_input"] = action_input_match.group(1).strip()
        
        return result
    
    def _tools_description(self) -> str:
        """Generate a description of available tools."""
        descriptions = []
        for name, tool in self.tools.items():
            descriptions.append(f"- {name}: {tool.description}")
        return "\n".join(descriptions)

    

def build_writer(research_report: str, topic: str) -> str:
    """
    the writer is NOT a ReAct agent - it has no tools and no loop.
    it is a simple LLM call: format the prompt with the reasearch output and call the model once to get the article.
    Why not make it an agent?
    An agent loop makes sense when the LLM needs to DECIDE what to do
    (call a tool, reason, retry). The writer has everything it needs
    upfront — there is no decision to make, just transformation.
    A direct LLM call is simpler, faster, and less error-prone.
    """
    llm = _make_llm(temperature=0.7) #more creative
    
    prompt_text = WRITER_PROMPT.format(research=research_report, topic=topic)

    # Direct invoke — no agent loop, just one LLM call
    response = llm.invoke(prompt_text)
    return response.content