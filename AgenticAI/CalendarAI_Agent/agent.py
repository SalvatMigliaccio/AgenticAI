from langchain_ollama import ChatOllama
from tools import ALL_TOOLS
import json
import re
import logging

logger = logging.getLogger(__name__)


def build_agent():
    """Build a custom agent that works with Ollama by manually parsing tool calls from text."""
    
    llm = ChatOllama(
        model="mistral",
        temperature=0,
    )

    class OllamaAgentExecutor:
        def __init__(self, llm, tools):
            self.llm = llm
            self.tools = {t.name: t for t in tools}
            self.max_iterations = 10

        def invoke(self, inputs):
            messages = inputs.get("messages", [])
            if not messages:
                query = inputs.get("input", "")
            else:
                query = messages[0].get("content", "") if isinstance(messages[0], dict) else str(messages[0])
            
            thought_action_log = ""
            last_action_signature = None
            repeated_action_count = 0
            last_observation = ""
            
            for iteration in range(self.max_iterations):
                # Costruisci il prompt con il ReAct format
                tools_list = "\n".join([f"- {t.name}: {t.description}" for t in ALL_TOOLS])
                
                full_prompt = f"""Sei un assistente intelligente che risolve compiti usando questi strumenti:

{tools_list}

Usa questo ESATTO formato per rispondere:

Thought: Pensa a quale azione intraprendere
Action: Il nome dello strumento da usare
Action Input: {{il json input per lo strumento}}
Observation: Il risultato dello strumento
... (ripeti se necessario)
Thought: Ho la risposta finale
Final Answer: La risposta in italiano per l'utente

{f"Precedenti azioni:" + thought_action_log if thought_action_log else ""}

Domanda: {query}"""
                
                logger.info(f"[Iter {iteration}] Calling LLM...")
                try:
                    response = self.llm.invoke(full_prompt)
                except KeyboardInterrupt:
                    logger.warning("LLM call interrupted by user")
                    if last_observation:
                        return {"output": last_observation}
                    return {"output": "Esecuzione interrotta dall'utente."}
                text = response.content
                logger.info(f"[Iter {iteration}] LLM response: {text[:200]}")
                
                # Parse della risposta - supporta anche frasi tipo "Utilizza create_calendar_event"
                action_line_match = re.search(r"Action:\s*(.+)", text, re.IGNORECASE)
                # Estrai tutto da Action Input fino alla fine o alla prossima sezione
                action_input_match = re.search(
                    r"Action Input:\s*(\{.+?)(?=\n\s*Observation:|$)",
                    text,
                    re.IGNORECASE | re.DOTALL
                )
                final_answer_match = re.search(r"Final Answer:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
                
                thought_action_log += f"\n{text}\n"
                
                # Check for valid action
                valid_action = None
                if action_line_match:
                    action_line = action_line_match.group(1).strip()
                    for tool_name in self.tools.keys():
                        if re.search(rf"\b{re.escape(tool_name)}\b", action_line):
                            valid_action = tool_name
                            break
                    if not valid_action:
                        logger.info(f"[Iter {iteration}] Action line '{action_line}' has no known tool")
                
                if final_answer_match and not valid_action:
                    # Solo se non abbiamo un'azione valida, considera il final answer
                    logger.info(f"[Iter {iteration}] Final answer found")
                    return {"output": final_answer_match.group(1).strip()}
                
                if valid_action and action_input_match:
                    action = valid_action
                    action_input_str = action_input_match.group(1).strip()
                    
                    logger.info(f"[Iter {iteration}] Action: {action}, Input: {action_input_str[:100]}")
                    
                    try:
                        action_input = json.loads(action_input_str)
                    except json.JSONDecodeError:
                        logger.warning(f"[Iter {iteration}] Failed to parse JSON: {action_input_str}")
                        action_input = {"text": action_input_str}
                    
                    # Esegui il tool
                    if action in self.tools:
                        tool = self.tools[action]
                        try:
                            action_signature = f"{action}:{json.dumps(action_input, sort_keys=True, ensure_ascii=False)}"
                            if action_signature == last_action_signature:
                                repeated_action_count += 1
                            else:
                                repeated_action_count = 0
                                last_action_signature = action_signature

                            if repeated_action_count >= 1:
                                logger.warning(f"[Iter {iteration}] Repeated action detected, stopping loop: {action_signature}")
                                if last_observation:
                                    return {"output": last_observation}
                                return {"output": "Ho rilevato un loop di azioni ripetute e ho interrotto l'esecuzione."}

                            logger.info(f"[Iter {iteration}] Executing tool '{action}' with input {action_input}")
                            observation = tool.func(**action_input)
                            last_observation = observation
                            logger.info(f"[Iter {iteration}] Tool result: {observation[:200]}")
                            thought_action_log += f"Observation: {observation}\n"

                            # Se l'evento calendario e stato creato, termina subito per evitare duplicati.
                            if action == "create_calendar_event" and observation.startswith("Evento '"):
                                return {"output": observation}
                        except TypeError as e:
                            logger.error(f"[Iter {iteration}] Tool call error: {e}")
                            thought_action_log += f"Observation: Errore nel tool: parametri non corretti - {e}\n"
                        except Exception as e:
                            logger.error(f"[Iter {iteration}] Tool error: {e}", exc_info=True)
                            thought_action_log += f"Observation: Errore nel tool: {e}\n"
                    else:
                        logger.warning(f"[Iter {iteration}] Tool '{action}' not found in {list(self.tools.keys())}")
                        thought_action_log += f"Observation: Tool '{action}' non trovato. Strumenti disponibili: {list(self.tools.keys())}\n"
                else:
                    logger.info(f"[Iter {iteration}] No action/input found, checking for final answer")
                    if text.strip() and len(text) > 50:
                        return {"output": text}
            
            logger.warning(f"Max iterazioni ({self.max_iterations}) raggiunto")
            return {"output": "Max iterazioni raggiunto senza risposta finale"}
    
    return OllamaAgentExecutor(llm=llm, tools=ALL_TOOLS)
