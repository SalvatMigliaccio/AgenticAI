# PDF RAG Agent — LangChain · Qdrant · Ollama

Applicazione **RAG (Retrieval-Augmented Generation)** full-stack che permette di caricare
uno o più PDF e fare domande in linguaggio naturale sul loro contenuto. Le risposte sono
generate da un LLM locale (Mistral via Ollama) **solo** sulla base del testo realmente
contenuto nei documenti, e ogni risposta riporta le **citazioni** (file + pagina) da cui
l'informazione è stata estratta.

Tutto gira in locale tramite Docker: nessun dato lascia la tua macchina e non servono
API key di servizi esterni.

---

## Indice

1. [Cos'è un RAG (e perché serve)](#cosè-un-rag-e-perché-serve)
2. [Le fasi del RAG, spiegate](#le-fasi-del-rag-spiegate)
   - [1. Loading (caricamento del documento)](#1-loading--caricamento-del-documento)
   - [2. Chunking (suddivisione in pezzi)](#2-chunking--suddivisione-in-pezzi)
   - [3. Embedding (trasformazione in vettori)](#3-embedding--trasformazione-in-vettori)
   - [4. Indexing / Storage (salvataggio nel vector DB)](#4-indexing--storage-salvataggio-nel-vector-db)
   - [5. Retrieval (recupero dei pezzi rilevanti)](#5-retrieval--recupero-dei-pezzi-rilevanti)
   - [6. Generation (generazione della risposta)](#6-generation--generazione-della-risposta)
3. [Architettura del progetto](#architettura-del-progetto)
4. [Struttura dei file](#struttura-dei-file)
5. [Come avviarlo](#come-avviarlo)
6. [API del backend](#api-del-backend)
7. [Configurazione](#configurazione)
8. [Note e limitazioni](#note-e-limitazioni)

---

## Cos'è un RAG (e perché serve)

Un LLM "puro" (come Mistral o GPT) conosce solo ciò che ha visto durante l'addestramento.
Non conosce **i tuoi** documenti, e se gli chiedi qualcosa che non sa tende a *inventare*
(fenomeno chiamato **hallucination**).

Il **RAG** risolve il problema così: invece di chiedere all'LLM "rispondi a memoria",
gli diamo prima **il pezzo di documento giusto** e poi gli chiediamo "rispondi *usando
questo testo*". In pratica trasformiamo l'LLM da "studente che va a memoria" a "studente
con il libro aperto davanti".

Il flusso si divide in due grandi momenti:

```
INGESTION (una volta, quando carichi i PDF)
  PDF → Loading → Chunking → Embedding → salvataggio nel Vector DB (Qdrant)

QUERY (ogni volta che fai una domanda)
  Domanda → Embedding della domanda → Retrieval dei chunk simili → 
            costruzione del prompt con il contesto → Generation della risposta
```

---

## Le fasi del RAG, spiegate

Qui descriviamo ogni fase **concettualmente** e poi indichiamo **dove** avviene nel codice.

### 1. Loading — caricamento del documento

**Cosa significa.** Un PDF non è testo "pulito": è un formato binario con pagine, font e
layout. La fase di *loading* estrae il testo grezzo dal file e lo accompagna con dei
**metadati** (da quale file proviene, a quale pagina).

**Dove avviene.** In [`backend/ingest.py`](backend/ingest.py) tramite `PyPDFLoader` di
LangChain:

```python
loader = PyPDFLoader(path)        # estrae il testo pagina per pagina
documents.extend(loader.load())   # ogni pagina diventa un Document con metadata {source, page}
```

I metadati `source` (nome file) e `page` (numero di pagina, 0-based) sono ciò che più tardi
permette di mostrare le **citazioni** nella chat.

---

### 2. Chunking — suddivisione in pezzi

**Cosa significa.** *Chunking* vuol dire spezzare il testo in **frammenti piccoli e
gestibili** (i "chunk"). Serve per due motivi:

- **Precisione del retrieval:** se cerchi una frase, è meglio recuperare il paragrafo
  giusto piuttosto che un capitolo intero di 30 pagine. Chunk piccoli = ricerca più mirata.
- **Limiti dell'LLM e dell'embedding:** i modelli hanno un limite di quanto testo possono
  elaborare in un colpo. Pezzi più piccoli ci stanno e si rappresentano meglio.

Due parametri chiave:

- **`chunk_size`** = quanto è grande ogni pezzo (qui **1000 caratteri**).
- **`chunk_overlap`** = quanti caratteri di **sovrapposizione** tra un pezzo e il successivo
  (qui **200**). L'overlap evita che una frase importante venga "tagliata a metà" sul
  confine tra due chunk: un po' di contesto viene ripetuto all'inizio del chunk seguente.

**Dove avviene.** Sempre in [`backend/ingest.py`](backend/ingest.py), con il
`RecursiveCharacterTextSplitter`:

```python
SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", "."]   # prova prima a tagliare sui paragrafi, poi sulle righe, poi sugli spazi
)
chunks = SPLITTER.split_documents(documents)
```

Il termine *"recursive"* indica che lo splitter prova a tagliare sui separatori in ordine
di preferenza: prima cerca di dividere sui doppi a-capo (paragrafi), e solo se i pezzi
restano troppo grandi scende ai separatori più piccoli. Così i tagli cadono in punti
"naturali" del testo invece che in mezzo a una parola.

---

### 3. Embedding — trasformazione in vettori

**Cosa significa.** Un *embedding* è la conversione di un testo in una **lista di numeri**
(un vettore). L'idea: testi con **significato simile** producono vettori **vicini** nello
spazio; testi con significato diverso producono vettori lontani.

Esempio intuitivo: le frasi *"il gatto dorme sul divano"* e *"il felino riposa sul sofà"*
hanno parole diverse ma significato quasi identico → i loro vettori saranno molto vicini.
È questo che permette la **ricerca semantica**: cerchiamo per *significato*, non per
corrispondenza esatta di parole.

In questo progetto ogni chunk viene trasformato in un vettore di **768 numeri**
(`EMBED_DIM = 768`) usando il modello **`nomic-embed-text`** servito da Ollama.

**Dove avviene.** La classe `OllamaEmbeddings` in [`backend/ingest.py`](backend/ingest.py)
(e duplicata in [`backend/agent.py`](backend/agent.py)) chiama via HTTP l'endpoint di
Ollama:

```python
embeddings.embed_query(chunk.page_content)   # testo → vettore di 768 float
```

Lo **stesso** modello di embedding viene usato in **entrambe** le fasi (ingestion e query):
è fondamentale, perché solo usando lo stesso modello i vettori dei chunk e quello della
domanda vivono nello stesso "spazio" e sono confrontabili.

---

### 4. Indexing / Storage (salvataggio nel vector DB)

**Cosa significa.** I vettori vanno salvati da qualche parte che sappia cercarli
**velocemente per similarità**. Un normale database non basta: serve un **vector database**.
Qui usiamo **Qdrant**.

Concetti Qdrant:

- **Collection:** è come una "tabella". Contiene tutti i vettori. Qui si chiama `pdf_docs`.
- **Point:** è una singola riga = un vettore + il suo **payload** (i dati associati). Nel
  nostro caso il payload contiene il **testo del chunk**, il **source** (file) e la **page**.
- **Distanza Cosine:** è il modo in cui Qdrant misura "quanto sono simili" due vettori.
  La distanza coseno guarda **l'angolo** tra i vettori (la loro *direzione*), ignorandone la
  lunghezza — è lo standard per il testo perché conta il significato, non quanto è lungo il
  testo.

**Dove avviene.** In [`backend/ingest.py`](backend/ingest.py):

```python
client.recreate_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE)
)
...
point = PointStruct(
    id=str(uuid.uuid4()),
    vector=embedding,
    payload={"content": chunk.page_content, "source": ..., "page": ...}
)
client.upsert(collection_name=COLLECTION, points=points)
```

> Nota: l'app tiene anche una seconda collection di servizio, `rag_tracking_state`, usata
> da [`backend/api.py`](backend/api.py) solo per **ricordare l'elenco dei PDF caricati** tra
> un riavvio e l'altro (non contiene contenuto dei documenti).

---

### 5. Retrieval — recupero dei pezzi rilevanti

**Cosa significa.** Quando l'utente fa una domanda, **non** la mandiamo subito all'LLM.
Prima:

1. trasformiamo la **domanda** in un vettore (stesso embedding della fase 3);
2. chiediamo a Qdrant: *"dammi i chunk i cui vettori sono più vicini a questo"*;
3. otteniamo i passaggi di testo più **semanticamente pertinenti** alla domanda.

Questo è il cuore del "Retrieval" in *Retrieval*-Augmented Generation.

**Dove avviene.** In [`backend/agent.py`](backend/agent.py), funzione `_retrieve_hits`:

- calcola l'embedding della domanda;
- interroga Qdrant (`query_points` / `search`) recuperando un ampio bacino di candidati;
- **filtra** i risultati tenendo solo i documenti effettivamente caricati
  (`allowed_sources`);
- applica una logica **round-robin** per garantire *diversità*: prende qualche chunk da
  ciascun documento invece di pescarli tutti dallo stesso file, utile quando si confrontano
  più PDF.

Ogni passaggio recuperato viene formattato con l'intestazione `Source: <file>` e
`Page: <n>`, in modo da poter ricostruire le citazioni a valle.

---

### 6. Generation — generazione della risposta

**Cosa significa.** Finalmente costruiamo il **prompt** per l'LLM mettendo insieme:

- un'istruzione di sistema (*"rispondi in italiano, usa SOLO il contesto, se non c'è dillo"*),
- la **domanda** dell'utente,
- il **contesto** = i chunk recuperati nella fase 5.

L'LLM (Mistral via Ollama) genera la risposta basandosi su quel contesto. Poiché gli diamo
il testo reale dei documenti, la risposta è ancorata ai fatti e si riducono le allucinazioni.

**Dove avviene.** In [`backend/agent.py`](backend/agent.py), dentro `SimpleAgent.invoke`:

```python
prompt = (
    "Sei un assistente RAG. Rispondi in italiano ... usando solo il contesto fornito. "
    "Se l'informazione non c'e, dillo esplicitamente.\n\n"
    f"Documenti disponibili: {docs_list}\n\n"
    f"Domanda: {question}\n\n"
    f"Contesto:\n{context}\n\n"
    "Risposta:"
)
answer = llm.call(prompt)
```

Le **citazioni** vengono poi estratte in [`backend/api.py`](backend/api.py) (endpoint
`/chat`): una regex scansiona l'output del tool cercando le coppie `Source:`/`Page:`,
rimuove i duplicati e converte la pagina da 0-based a 1-based per la visualizzazione.

---

## Architettura del progetto

```
┌──────────────┐      HTTP       ┌──────────────┐
│   Frontend   │ ──────────────> │   Backend    │
│ React + Vite │   /upload       │   FastAPI    │
│  (porta 5173)│   /chat         │ (porta 8000) │
└──────────────┘ <────────────── └──────┬───────┘
                                         │
                        ┌────────────────┴────────────────┐
                        │                                  │
                  ┌─────▼──────┐                    ┌──────▼──────┐
                  │   Qdrant   │                    │   Ollama    │
                  │ Vector DB  │                    │ LLM + Embed │
                  │ (porta 6333)│                   │(porta 11434)│
                  └────────────┘                    └─────────────┘
                                              mistral · nomic-embed-text
```

Quattro container orchestrati da [`docker-compose.yml`](docker-compose.yml):

| Servizio   | Ruolo                                                        | Porta host |
|------------|-------------------------------------------------------------|------------|
| `frontend` | UI React (chat + upload), servita da Nginx                  | 5173       |
| `backend`  | API FastAPI: ingestion, retrieval, generation               | 8000       |
| `qdrant`   | Vector database che conserva i chunk vettorializzati        | 6333       |
| `ollama`   | Esegue in locale l'LLM (`mistral`) e l'embedder (`nomic`)   | 11435→11434|

---

## Struttura dei file

```
Langchain_qdrant_RAG/
├── docker-compose.yml          # orchestrazione dei 4 servizi
├── backend/
│   ├── api.py                  # FastAPI: endpoint /upload, /chat, /health, /tracked-documents
│   ├── ingest.py               # Loading + Chunking + Embedding + Storage (fasi 1-4)
│   ├── agent.py                # Retrieval + Generation (fasi 5-6) + client Ollama
│   ├── requirements.txt        # dipendenze Python
│   ├── Dockerfile              # immagine del backend
│   └── .env.example            # template variabili d'ambiente
└── frontend/
    ├── src/App.jsx             # tutta la UI (sidebar upload + chat con citazioni)
    ├── package.json            # dipendenze React/Vite
    ├── Dockerfile              # build + Nginx
    └── nginx.conf              # serve la SPA
```

**Mappa "fase RAG → file":**

| Fase                | File principale            |
|---------------------|----------------------------|
| Loading             | `backend/ingest.py`        |
| Chunking            | `backend/ingest.py`        |
| Embedding           | `backend/ingest.py` / `backend/agent.py` |
| Indexing / Storage  | `backend/ingest.py`        |
| Retrieval           | `backend/agent.py`         |
| Generation          | `backend/agent.py`         |
| Orchestrazione API  | `backend/api.py`           |
| Interfaccia utente  | `frontend/src/App.jsx`     |

---

## Come avviarlo

### Prerequisiti
- Docker e Docker Compose installati.
- (Opzionale ma consigliato) GPU NVIDIA per velocizzare Ollama — vedi la sezione commentata
  in [`docker-compose.yml`](docker-compose.yml).

### Passi

1. **Configura le variabili d'ambiente** del backend:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **Avvia tutti i servizi:**
   ```bash
   docker compose up -d --build
   ```

3. **Scarica i modelli dentro Ollama** (solo la prima volta — i pesi vengono salvati nel
   volume `ollama_data`):
   ```bash
   docker exec -it ollama ollama pull mistral
   docker exec -it ollama ollama pull nomic-embed-text
   ```

4. **Apri l'app:** [http://localhost:5173](http://localhost:5173)

5. Dalla sidebar **carica uno o più PDF**, attendi l'indicizzazione, poi **fai una domanda**.

> **Ingestion da riga di comando (bulk):** per indicizzare un'intera cartella di PDF senza
> passare dalla UI:
> ```bash
> docker exec -it backend python ingest.py ./percorso/cartella_pdf
> ```

---

## API del backend

Base URL: `http://localhost:8000`

| Metodo | Endpoint              | Descrizione                                                            |
|--------|-----------------------|------------------------------------------------------------------------|
| `GET`  | `/health`             | Healthcheck, ritorna `{"status":"ok"}`.                                |
| `POST` | `/upload`             | Carica uno o più PDF (multipart `files`). Esegue le fasi 1-4 e ritorna il numero di chunk indicizzati. |
| `POST` | `/chat`               | Body `{"question": "..."}`. Esegue retrieval + generation e ritorna `{answer, sources[]}`. |
| `GET`  | `/tracked-documents`  | Elenco dei PDF attualmente indicizzati.                                |

Esempio risposta `/chat`:
```json
{
  "answer": "Il documento descrive ...",
  "sources": [
    { "file": "manuale.pdf", "page": 3 },
    { "file": "manuale.pdf", "page": 7 }
  ]
}
```

---

## Configurazione

Variabili in [`backend/.env`](backend/.env.example):

| Variabile           | Default (Docker)        | Significato                                  |
|---------------------|-------------------------|----------------------------------------------|
| `QDRANT_URL`        | `http://qdrant:6333`    | URL del vector database.                      |
| `QDRANT_COLLECTION` | `pdf_docs`              | Nome della collection dei chunk.              |
| `OLLAMA_URL`        | `http://ollama:11434`   | URL del server Ollama (LLM + embeddings).     |

> Dentro Docker gli URL usano i **nomi dei servizi** (`qdrant`, `ollama`), non `localhost`,
> perché i container si parlano tra loro per nome. Se esegui il backend fuori da Docker,
> usa `http://localhost:6333` e `http://localhost:11435`.

Parametri "fissi" nel codice ([`backend/ingest.py`](backend/ingest.py)) che puoi voler
modificare per fare tuning del RAG:

- `chunk_size = 1000`, `chunk_overlap = 200` — granularità del chunking.
- `EMBED_MODEL = "nomic-embed-text"`, `EMBED_DIM = 768` — modello e dimensione embedding.
- `model = "mistral"` (in [`backend/agent.py`](backend/agent.py)) — LLM di generazione.

---

## Note e limitazioni

- **Solo PDF:** l'upload accetta esclusivamente file `.pdf` (controllo in
  [`backend/api.py`](backend/api.py)).
- **"Agent" semplificato:** nonostante il nome, `build_agent` non implementa un vero loop
  ReAct. Restituisce un `SimpleAgent` che fa *sempre* un singolo retrieval seguito da una
  singola generation. Lo strumento `cerca_nei_pdf` è definito ma il loop decisionale
  dell'LLM non è attivo (vedi commento nel file). È un punto naturale di evoluzione del
  progetto.
- **`OllamaEmbeddings` duplicata:** la stessa classe è definita sia in `ingest.py` sia in
  `agent.py`. Andrebbe centralizzata in un modulo condiviso.
- **`recreate_collection`:** in `_ensure_collection` la collection viene creata se assente,
  ma attenzione che `recreate_collection` **azzera** la collection se già esistente — qui è
  protetta da un controllo `if COLLECTION not in exists`.
- **CORS aperto:** `allow_origins=["*"]` va bene in sviluppo locale, ma andrebbe ristretto
  in produzione.
- **Tutto locale:** non servono chiavi API e nessun dato esce dalla macchina; in compenso
  le prestazioni dipendono dall'hardware (l'uso della GPU velocizza molto Ollama).
