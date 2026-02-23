
import requests


def get_race(weekend_id=None):
    """Ottiene il risultato della gara più recente da Ergast API"""
    try:
        url = f'https://api.jolpi.ca/ergast/f1/current/{weekend_id}/results.json' if weekend_id else 'https://api.jolpi.ca/ergast/f1/current/last/results.json'

        if weekend_id == 100:
            #testing api
            url = f'https://api.jolpi.ca/ergast/f1/2025/11/results.json'

        response = requests.get(url, timeout=10)
        data = response.json()
        print(data)  # Debug: mostra la risposta completa
        
        if 'MRData' not in data or 'RaceTable' not in data['MRData']:
            print("❌ Nessuna gara trovata su Ergast API")
            return None
        
        races = data['MRData']['RaceTable']['Races']
        if not races:
            print("❌ Nessun risultato disponibile")
            return None
        
        race = races[0]
        print(f"✅ Caricata gara: {race['raceName']} ({race['date']})")
        return race
    except Exception as e:
        print(f"❌ Errore nel caricamento da Ergast API: {e}")
        return None