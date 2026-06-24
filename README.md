# AgenticAI

Repository di studio e sperimentazione su Agentic AI e architetture multi-agent.

## Obiettivo

Questa repository raccoglie prototipi pratici per:
- studiare pattern Agentic AI
- testare workflow multi-agent
- confrontare approcci diversi su task reali
- costruire una base riusabile per esperimenti futuri

## Visione della repository

Questa repo non ospita un unico prodotto, ma una collezione di prototipi organizzati per area di ricerca.
L'obiettivo e avere piu cartelle indipendenti, ciascuna focalizzata su uno scenario specifico (agenti, tool use, RAG, orchestrazione), in modo da facilitare testing, confronto e apprendimento.

## Prototipi presenti

| Cartella | Obiettivo | Stato |
| --- | --- | --- |
| AgenticAI/CalendarAI_Agent | Prototipo agentico con tool esterni per calendario e meteo | In sviluppo |
| AgenticAI/example | Esempi minimi per esperimenti rapidi | In sviluppo |
| RAG/Langchain/QA_RAG | Prototipo RAG semplice su PDF per studio del flusso end-to-end | In sviluppo |
| RAG/Langchain/Langchain_qdrant_RAG | Prototipo RAG piu strutturato con backend e frontend | In sviluppo |

## Focus su Agentic AI e Multi-Agent

La parte principale del progetto e lo studio del comportamento agentico:
- orchestrazione di agenti con compiti distinti
- integrazione di tool esterni per eseguire azioni reali
- gestione dei loop decisionali in stile ReAct
- valutazione del comportamento in scenari semplici e complessi

## Tool utilizzati

Di seguito i principali tool e componenti usati nei prototipi. in ordine di utilizzo:

### LLM e inferenza
- Ollama: esecuzione locale di modelli LLM
- Mistral: modello usato in alcuni agenti locali
- Groq: provider per inferenza remota nei prototipi QA

### Framework agentici e RAG
- LangChain: orchestrazione agenti, tool calling e pipeline RAG
- LangChain Community/Core: componenti per loader, tool e integrazione

### Embeddings e retrieval
- Nomic embed text via Ollama: embeddings locali
- HuggingFace Embeddings: embeddings sentence-transformers
- Qdrant: vector database per ricerca semantica
- InMemoryVectorStore: archivio vettoriale leggero per test veloci

### Tool esterni integrati dagli agenti
- Google Calendar API: creazione eventi da agente
- OpenWeatherMap API: meteo e verifica pioggia

### Infrastruttura applicativa
- FastAPI + Uvicorn: backend API
- React + Vite: frontend per interfacce di test
- Docker + Docker Compose: ambiente locale riproducibile

### Utility dati
- PyPDF: parsing di documenti PDF
- Python dotenv: gestione variabili ambiente

## Struttura e convenzioni

Ogni prototipo puo includere:
- codice sorgente
- file requirements o package manager equivalenti
- README locale con scopo e istruzioni di avvio
- script di test o demo

## Stato del progetto

Work in progress: la struttura evolvera con nuovi prototipi e refactor incrementali.

## Nota

Questa repository e pensata per studio, testing e iterazione rapida, non come prodotto finale unico.
