import os
import logging
from datetime import datetime, timedelta
from langchain.tools import tool
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")

def get_google_service():
    """
    Authenticate and return the Google Calendar API service.
    """
    logger.info(f"TOKEN_PATH: {TOKEN_PATH}")
    logger.info(f"CREDENTIALS_PATH: {CREDENTIALS_PATH}")
    logger.info(f"Token exists: {os.path.exists(TOKEN_PATH)}")
    logger.info(f"Credentials exists: {os.path.exists(CREDENTIALS_PATH)}")
    
    creds = None
    if os.path.exists(TOKEN_PATH):
        logger.info("Loading existing token...")
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        
    if not creds or not creds.valid:
        logger.info(f"Creds valid: {creds.valid if creds else False}")
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token...")
            creds.refresh(Request())
        else:
            logger.info("Running OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        logger.info("Saving token...")
        with open(TOKEN_PATH, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)

@tool
def create_calendar_event(title: str, start_time: str, end_time: str = "") -> str:
    """
    Crea un evento su Google Calendar con orari ISO locali.
    Input:
      - title: titolo (es. "Dentista")
      - start_time: formato YYYY-MM-DD HH:MM (es. "2026-07-25 15:30")
      - end_time: opzionale, formato YYYY-MM-DD HH:MM (es. "2026-07-25 16:30")
        Se omesso, viene usata una durata predefinita di 1 ora.
    """
    logger.info(f"create_calendar_event called: title={title}, start={start_time}, end={end_time}")
    try:
        service = get_google_service()
        logger.info("Service obtained")
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
        logger.info(f"Parsed start_dt: {start_dt}")
        end_dt = (
            datetime.strptime(end_time, "%Y-%m-%d %H:%M")
            if end_time.strip()
            else start_dt + timedelta(hours=1)
        )

        if end_dt <= start_dt:
            return "Errore: end_time deve essere successivo a start_time."
        
        event = {
            "summary": title,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Europe/Rome"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Europe/Rome"},
        }
        logger.info(f"Inserting event: {event}")
        created = service.events().insert(calendarId="primary", body=event).execute()
        result = (
            f"Evento '{title}' creato dal {start_dt.strftime('%Y-%m-%d %H:%M')} "
            f"al {end_dt.strftime('%Y-%m-%d %H:%M')}. "
            f"Link: {created.get('htmlLink')}"
        )
        logger.info(f"Event created successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in create_calendar_event: {type(e).__name__}: {e}", exc_info=True)
        return f"Errore: {e}"
    
    