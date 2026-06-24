import logging
import json
from agent import build_agent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_test():
    agent = build_agent()
    user_input = "Crea un appuntamento dal dentista per il 25 luglio 2026 alle 15:30."
    print(f"Running query: {user_input}")
    
    result = agent.invoke({"input": user_input})
    
    print("\n--- RETURNED DICT ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("---------------------\n")

if __name__ == "__main__":
    run_test()
