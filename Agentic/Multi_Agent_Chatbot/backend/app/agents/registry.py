from dataclasses import dataclass, field
from app.core.config import settings


@dataclass(frozen=True)
class DomainAgent:
    key: str                     # identificatore interno (= valore di state["route"])
    label: str                   # nome leggibile (mostrato nel frontend)
    description: str             # usato dal classificatore LLM di fallback
    model: str                   # ← vLLM: nome adapter LoRA, o il base model
    use_rag: bool                # questo dominio recupera contesto da Qdrant?
    collection: str | None       # nome della collection Qdrant (se use_rag)
    # Frasi-esempio del dominio: il router le converte in embedding e ne fa il
    # "centroide". La query viene assegnata al dominio col centroide più vicino.
    exemplars: list[str] = field(default_factory=list)


# --- I nostri agent. Per aggiungerne uno, aggiungi una riga qui. ---
REGISTRY: dict[str, DomainAgent] = {
    "crypto_pqc": DomainAgent(
        key="crypto_pqc",
        label="Crittografia & Post-Quantum",
        description="Crittografia classica e post-quantum: RSA, ECC, ML-KEM, "
                    "ML-DSA, SLH-DSA, hash, firme, migrazione PQC, CBOM.",
        model="crypto-pqc-lora",          # ← vLLM: adapter LoRA caricato accanto al base
        use_rag=True,
        collection="kb_crypto",
        exemplars=[
            "Qual è la differenza tra ML-KEM e ML-DSA?",
            "Come si pianifica la migrazione da RSA a crittografia post-quantum?",
            "Spiegami SLH-DSA e i suoi parametri di sicurezza.",
            "Cos'è un CBOM e a cosa serve nella crypto-agility?",
        ],
    ),
    "eidas_compliance": DomainAgent(
        key="eidas_compliance",
        label="eIDAS2 & Trust Services",
        description="eIDAS2, EUDI Wallet, firme qualificate, QTSP, LoA, "
                    "attestati di attributi, conformità e regolamentazione UE.",
        model="eidas-lora",               # ← vLLM
        use_rag=True,
        collection="kb_eidas",
        exemplars=[
            "Che differenza c'è tra firma FES, FEA e QES?",
            "Quali sono i livelli di garanzia (LoA) in eIDAS?",
            "Come funziona il key binding in un SD-JWT VC?",
            "Cosa deve garantire un QTSP per emettere attestati qualificati?",
        ],
    ),
    "software_eng": DomainAgent(
        key="software_eng",
        label="Ingegneria del Software",
        description="Programmazione, architetture, API, Python, design pattern, "
                    "testing, Docker, debugging.",
        model="software-eng-lora",        # ← vLLM
        use_rag=False,                    # esempio di dominio SENZA RAG
        collection=None,
        exemplars=[
            "Come strutturo un'app FastAPI scalabile?",
            "Scrivimi un test asincrono con pytest.",
            "Qual è la differenza tra processi e thread in Python?",
            "Come ottimizzo una query SQL lenta?",
        ],
    ),
    # Fallback: NESSUN adapter, usa il base model. Rete di sicurezza quando la
    # domanda non rientra in nessun dominio specialistico.
    "general": DomainAgent(
        key="general",
        label="Generalista",
        description="Domande generiche non coperte dagli altri domini.",
        model=settings.LLM_BASE_MODEL,    # base model, nessun adapter
        use_rag=False,
        collection=None,
        exemplars=[],                     # nessun esemplare: non compete nel routing
    ),
}

# Dominio di fallback quando il router non è sicuro e nemmeno l'LLM decide.
FALLBACK_KEY = "general"


def specialist_keys() -> list[str]:
    """Domini che competono nel routing per similarità (escluso il generalista)."""
    return [k for k, a in REGISTRY.items() if a.exemplars]


def get_agent(key: str) -> DomainAgent:
    """Ritorna l'agent richiesto, o il fallback se la chiave non esiste."""
    return REGISTRY.get(key, REGISTRY[FALLBACK_KEY])

def resolve_model(agent: DomainAgent) -> str:
    """Nome del modello da passare a provider.chat() per uno specialista.

    In dev (USE_ADAPTERS=False) ritorna sempre il base model, così puoi costruire
    e testare l'intero grafo PRIMA di aver fatto il fine-tuning. In prod
    (USE_ADAPTERS=True) ritorna l'adapter LoRA specifico del dominio.
    """
    if not settings.USE_ADAPTERS:
        return settings.LLM_BASE_MODEL
    return agent.model