# CalendarAI Agent

Agente AI locale che interpreta richieste in linguaggio naturale e usa tool reali per:

- leggere il meteo con OpenWeatherMap
- verificare condizioni di pioggia
- creare eventi su Google Calendar

Stack: Python + Ollama (`mistral`) + Google Calendar API + OpenWeatherMap.

## Demo in 60 secondi

```powershell
cd CalendarAI_Agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\main.py
```

## Cosa fa

- Tool meteo: `get_weather`, `check_if_rain`
- Tool calendario: `create_calendar_event`
- Loop ReAct con parser custom delle azioni del modello
- Logging completo per debug passo-passo

## Struttura progetto

```text
CalendarAI_Agent/
  agent.py
  main.py
  requirements.txt
  .env
  credentials.json
  token.json
  tools/
    __init__.py
    weather.py
    calendar.py
```

## Configurazione

### 1) Variabili ambiente

File `.env`:

```env
OPENWEATHERMAP_API_KEY="la_tua_chiave"
```

### 2) Ollama

```powershell
ollama pull mistral
ollama serve
```

### 3) Google Calendar OAuth

Metti `credentials.json` in `CalendarAI_Agent/`.

Al primo uso del tool calendario viene aperto il browser e generato `token.json`.

Se ricevi `Error 403: access_denied`:

1. Apri Google Cloud Console
2. Vai in APIs & Services -> OAuth consent screen
3. In Test users aggiungi la tua email
4. Riprova login con lo stesso account

## Uso

```powershell
python .\main.py
```

Le query demo incluse sono:

- controllo meteo condizionale (se piove)
- creazione evento dentista

Formato date per calendario:

- `start_time`: `YYYY-MM-DD HH:MM`
- `end_time` opzionale (default `+1 ora`)
- timezone: `Europe/Rome`

## Architettura (high level)

1. `main.py` invia la query all'agente
2. `agent.py` chiede al modello una risposta ReAct
3. Il parser estrae `Action` e `Action Input`
4. Viene eseguito il tool corretto
5. L'osservazione rientra nel loop fino alla risposta finale

## Troubleshooting rapido

### "Nessuna risposta generata"

- controlla i log `INFO`
- verifica che l'agente ritorni `output`

### Il modello scrive "Utilizza create_calendar_event" ma non chiama il tool

- assicurati di avere l'ultima versione di `agent.py` con parsing action line robusto

### Evento non creato su Google Calendar

- verifica `credentials.json`
- elimina `token.json` e rifai autorizzazione
- assicurati di essere tra i Test users OAuth

### OpenWeather non risponde

- controlla il nome variabile: `OPENWEATHERMAP_API_KEY`

### Windows Unicode error

```powershell
$env:PYTHONIOENCODING='utf-8'
python .\main.py
```

## Sicurezza

Non versionare mai:

- `.env`
- `credentials.json`
- `token.json`
- `.venv/`

## Roadmap

- Migrare a tool-calling nativo con modello piu affidabile
- Aggiungere parser date naturali in italiano
- Aggiungere test automatici per parser e tool layer
- Supportare luogo/descrizione/eventi all-day

