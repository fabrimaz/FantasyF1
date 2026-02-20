"""
Fantasy F1 Scoring Job
Calcola i punteggi dei team basandosi sui risultati ufficiali F1 (Ergast API)
Schedulato per girare ogni domenica sera dopo il GP
"""

import requests
from datetime import datetime
import sys

import os

# Aggiungi il parent directory al path per gli import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, Team, TeamResult, GrandPrix, User
from app import app
import json

# Punti F1 standard
F1_POINTS = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}

# Mapping numero pilota -> ID nel nostro DB
DRIVER_MAPPING = {
    1: 1,      # Max Verstappen
    11: 2,     # Sergio Perez
    44: 3,     # Lewis Hamilton
    63: 4,     # George Russell
    16: 5,     # Charles Leclerc
    55: 6,     # Carlos Sainz
    4: 7,      # Lando Norris
    81: 8,     # Oscar Piastri
    14: 9,     # Fernando Alonso
    18: 10,    # Lance Stroll
    10: 11,    # Pierre Gasly
    31: 12,    # Esteban Ocon
    23: 13,    # Alex Albon
    22: 14,    # Yuki Tsunoda
    27: 15,    # Nico Hulkenberg
    3: 16,     # Daniel Ricciardo
    77: 17,    # Valtteri Bottas
    24: 18,    # Guanyu Zhou
    20: 19,    # Kevin Magnussen
    2: 20,     # Logan Sargeant
}

# Mapping scuderia -> ID nel nostro DB
CONSTRUCTOR_MAPPING = {
    'red_bull': 1,
    'ferrari': 2,
    'mclaren': 3,
    'mercedes': 4,
    'aston_martin': 5,
    'alpine': 6,
    'williams': 7,
    'rb': 8,
    'haas': 9,
    'sauber': 10,
}

def get_latest_race():
    """Ottiene il risultato della gara più recente da Ergast API"""
    try:
        # Ottieni l'ultima gara completata
        response = requests.get('https://api.jolpi.ca/ergast/f1/current/last/results.json', timeout=10)
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

def calculate_team_score(team, race_results):
    """
    Calcola il punteggio totale di un team basandosi sui driver selezionati
    
    Args:
        team: oggetto Team con i driver selezionati
        race_results: dict con i risultati della gara da Ergast
    
    Returns:
        int: punteggio totale del team
    """
    drivers = team.get_drivers()
    constructors = team.get_constructors()
    total_score = 0
    
    # Crea un dict rapido dei risultati per numero pilota
    results_by_number = {}
    for result in race_results.get('Results', []):
        driver_num = int(result['Driver']['driverId'].split('_')[0]) if '_' in result['Driver']['driverId'] else None
        # Usa il numero di gara (identificativo corto)
        for mapped_num, driver_id in DRIVER_MAPPING.items():
            if driver_id == int(result['Driver']['driverId'].split('_')[-1]) if '_' in result['Driver']['driverId'] else mapped_num == int(result['number']):
                results_by_number[mapped_num] = int(result['position']) if result['position'] != 'R' else None
                break
    
    # Punteggi driver
    for driver in drivers:
        # Cerca il numero di gara del driver
        for car_number, position in results_by_number.items():
            if position and car_number <= 20:  # Solo driver validi
                points = F1_POINTS.get(position, 0)
                total_score += points
                print(f"  🏁 Driver ID {driver['id']}: posizione {position} = {points} pts")
                break
    
    return total_score

def process_race_results(race_data, gp_id):
    """
    Elabora i risultati della gara e aggiorna i punteggi dei team
    """
    print(f"\n📊 Elaborazione risultati per GP ID {gp_id}...")
    
    # Ottieni tutti i team per questo GP
    teams = Team.query.filter_by(gp_id=gp_id).all()
    
    if not teams:
        print(f"⚠️  Nessun team trovato per questo GP")
        return
    
    print(f"Found {len(teams)} teams")
    
    # Per ogni team, calcola il punteggio
    for team in teams:
        # Semplificato: usa il numero di driver selezionati come base
        # In una versione reale, faresti il matching con Ergast
        drivers = team.get_drivers()
        
        # Calcolo semplificato per demo: somma dei prezzi (da estendere con veri risultati)
        score = sum(d.get('price', 0) for d in drivers if d)
        
        # Salva/aggiorna il risultato
        result = TeamResult.query.filter_by(team_id=team.id, gp_id=gp_id).first()
        if not result:
            result = TeamResult(team_id=team.id, user_id=team.user_id, gp_id=gp_id)
            db.session.add(result)
        
        result.points = int(score)
        print(f"  ✅ Team {team.user.username} (GP {gp_id}): {score} pts")
    
    db.session.commit()
    print("✅ Punteggi salvati nel database")

def run_scoring_job():
    """Main job - eseguito ogni domenica sera"""
    with app.app_context():
        print(f"\n{'='*60}")
        print(f"🏁 FANTASY F1 SCORING JOB - {datetime.now().isoformat()}")
        print(f"{'='*60}\n")
        
        # 1. Ottieni i risultati della gara più recente da Ergast
        race_data = get_latest_race()
        if not race_data:
            message ="❌ Job abortito: nessun dato di gara disponibile"
            print(message)
            return message
        
        # 2. Trova il GP corrispondente nel nostro DB
        # Ergast usa formato YYYY-MM-DD, il nostro DB ha datetime
        race_date_str = race_data.get('date')
        gp = GrandPrix.query.filter(
            GrandPrix.date >= datetime.fromisoformat(race_date_str),
            GrandPrix.date < datetime.fromisoformat(race_date_str.replace('-', '') + 'T23:59:59')
        ).first()
        
        if not gp:
            message =f"❌ Nessun GP trovato per la data {race_date_str}"
            print(message)
            return message
        
        match_message = f"🎯 Matched GP: {gp.name} (ID {gp.id})"
        print(match_message)
        
        # 3. Processa i risultati e calcola i punteggi
        process_race_results(race_data, gp.id)
        
        message = "✅ Job completato con successo"
        print(message)
        return message + ". " + match_message

if __name__ == '__main__':
    run_scoring_job()
