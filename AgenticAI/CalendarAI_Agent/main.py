import logging
from dotenv import load_dotenv
from agent import build_agent
from langchain_core.messages import AIMessage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()


def run(query: str) -> None:
    agent = build_agent()
    print(f"\n{'─'*60}\n  QUERY: {query}\n{'─'*60}")
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})

    output = result.get("output", "")
    if not output:
        output = "Nessuna risposta generata."
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage):
                output = msg.content
                break

    print(f"\n  RISPOSTA FINALE: {output}\n")


if __name__ == "__main__":
    run(
        "Controlla se pioverà a Napoli domani. "
        "Se piove, crea un evento 'Smart working' il 2026-05-20 alle 10:00."
    )

    run("Crea un appuntamento dal dentista per il 25 luglio 2026 alle 15:30.")