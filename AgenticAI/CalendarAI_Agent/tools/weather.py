import os
import requests
from langchain.tools import tool

@tool
def get_weather(city: str, **kwargs) -> str:
    """
    Recuperare le condizioni meteo della città, utilizzare solo quando l'utente chiede il meteo, 
    la temperatura o le condizioni atmosferiche di un luogo. Devi fornire in uscita non solo il meteo generico (come soleggiati, nuvoloso etc) ma anche tutte le informazioni associate, come vento temperatura massima, minima etc..
    Input: nome della città in italiano (es. 'Roma', 'Milano').
    """
    API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    if not API_KEY:
        return "Errore: chiave API non trovata. Assicurati di impostare la variabile d'ambiente OPENWEATHERMAP_API_KEY."
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "it"
    }
    
    try: 
        response = requests.get(url, params=params)
        response.raise_for_status()
        d = response.json()
        return (
            f"Il meteo a {city} è {d['weather'][0]['description']} con una temperatura di {d['main']['temp']}°C. "
            f"Temperatura massima: {d['main']['temp_max']}°C, temperatura minima: {d['main']['temp_min']}°C. "
            f"Vento: {d['wind']['speed']} m/s, umidità: {d['main']['humidity']}%."
        )
    except requests.exceptions.RequestException as e:
        return f"Errore nella richiesta: {e}"
    
@tool
def check_if_rain(city: str, **kwargs) -> str:
    """
    Controlla se sta piovendo nella città specificata. Utilizza solo quando l'utente chiede se sta piovendo o se ci sono condizioni di pioggia.
    Input: nome della città in italiano (es. 'Roma', 'Milano').
    """
    API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    if not API_KEY:
        return "Errore: chiave API non trovata. Assicurati di impostare la variabile d'ambiente OPENWEATHERMAP_API_KEY."
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
    }
    
    try: 
        response = requests.get(url, params=params, timeout=10)
        d = response.json()
        weather_id = d['weather'][0]['id']
        description = d['weather'][0]['description']
        
        if weather_id < 600:
            return f"Sì, sta piovendo a {city}. Condizioni: {description}."
        return f"No, non sta piovendo a {city}. Condizioni: {description}."
    except requests.exceptions.RequestException as e:
        return f"Errore nella richiesta: {e}"
    
        