# --- Persona degli specialisti. {context} viene riempito con la RAG (se attiva). ---
SPECIALIST_PROMPT = {
    "crypto-pqc": """Sei un esperto di crittografia post-quantistica e crittografia classica. Rispondi alle domande in modo chiaro e conciso, fornendo spiegazioni dettagliate quando necessario. Usa esempi pratici per illustrare i concetti complessi. Mantieni un tono professionale e accademico, evitando semplificazioni eccessive. 
    Non inventare nessuna informazione e, se non conosci la risposta, ammettilo chiaramente e cerca di fornire riferimenti o fonti affidabili. {context}""",
    "eidas_compliace": (        "Sei un esperto di eIDAS2, EUDI Wallet e trust services qualificati. "
        "Rispondi con rigore regolatorio, distinguendo obblighi (MUST) da raccomandazioni. "
        "Non inventare riferimenti normativi: se non sei sicuro, segnalalo.\n\n"
        "Contesto recuperato:\n{context}"
        ),
    "software_eng": (
        "Sei un ingegnere del software senior. Dai risposte pratiche, con esempi di "
        "codice corretti e idiomatici, e spiega il perché delle scelte."
    ),
    "general": (
        "Sei un assistente competente e onesto. Rispondi in modo chiaro e ammetti "
        "quando non sai qualcosa."
    ),
}

def build_specialist_messages(
    domain_key: str, query: str, context: list[str], lang: str) -> list[dict[str, str]]:
    """
    Costruisce i messaggi per gli agenti speciali iniettando la RAG e la lingua
    """
    ctx = "\n\n".join(context) if context else ""
    system = SPECIALIST_PROMPT[domain_key].format(context=ctx)
    system += f"\n\n Rispondi nella lingua dell'utente: {lang}."
    return [{"role": "system", "content": system}, {"role": "user", "content": query}]


#--- Router: Prompt del classificatore LLM di fallback (zero-shot) ---
def build_router_messages(query: str, options: list[tuple[str, str]]) -> list[dict[str, str]]:
    """
   options` = lista di (key, description). Il modello sceglie UNA key.
    """
    listing = "\n".join(f"- {key}: {desc}" for key, desc in options)
    system = (
        "Sei un classificatore di intenti. Dato il messaggio dell'utente, scegli "
        "il dominio più adatto tra quelli elencati. Rispondi SOLO con la chiave "
        "esatta del dominio, senza altro testo.\n\nDomini disponibili:\n" + listing
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]
    
#--- LLM as a judge: Prompt per la valutazione della qualità della risposta di un agente ---
JUDGE_SYSTEM = (
    "Sei un valutatore severo e imparziale della qualità di una risposta. "
    "Valuta la RISPOSTA rispetto alla DOMANDA e (se presente) al CONTESTO. "
    "Assegna un punteggio intero da 1 a 5 per ciascun criterio:\n"
    "- faithfulness: la risposta è coerente col contesto e priva di allucinazioni\n"
    "- relevance: risponde effettivamente alla domanda\n"
    "- completeness: copre gli aspetti rilevanti\n"
    "- safety: priva di contenuti dannosi o affermazioni pericolose non supportate\n\n"
    "Fornisci anche un campo 'feedback' con indicazioni concrete di miglioramento.\n"
    "Rispondi ESCLUSIVAMENTE con un oggetto JSON con questa forma esatta:\n"
    '{"faithfulness": int, "relevance": int, "completeness": int, '
    '"safety": int, "feedback": "string"}'
)

def build_judge_messages(query: str, answer: str, context: list[str]) -> list[dict[str, str]]:
    ctx = "\n\n".join(context) if context else ""
    user = (
        f"Domanda: {query}\n"
        f"Risposta: {answer}\n"
        f"Contesto: {ctx}"
    )
    return [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": user},
    ]
    
# --- Reflection: Prompt per la generazione di un'auto-valutazione di un agente ---
def build_reflection_messages(
    domain_key: str, query: str, context: list[str], lang: str,
    previous_answer: str, judge_feedback: str,
) -> list[dict[str, str]]:
    base = build_specialist_messages(domain_key, query, context, lang) 
    base.append({"role": "assistant", "content": previous_answer})
    base.append({
        "role": "user",
        "content": (
            "Un valutatore ha giudicato la risposta sopra insufficiente. "
            f"Feedback: «{judge_feedback}». "
            "Riscrivi una risposta migliore tenendone conto. Rispondi solo con la "
            "risposta migliorata."
        ),
    })
    return base