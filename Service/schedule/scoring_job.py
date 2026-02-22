"""
Fantasy F1 Scoring Job
Calcola i punteggi dei team basandosi sui risultati ufficiali F1 (Ergast API)
Schedulato per girare ogni domenica sera dopo il GP o chiamata da API
"""

from turtle import position

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
FantasyF1_POINTS = {
    1: 50, 2: 36, 3: 30, 4: 24, 5: 20,
    6: 16, 7: 12, 8: 8, 9: 4, 10: 2,
    11:1, 12: 1, 13: 0, 14: 0, 15: 0, 
    16: 0, 17: 0, 18: 0, 19: 0, 20: 0,
    -10: -10,  # Ritiro
    -1: -1    # Non partito (W)
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
    
    # Crea un dict <pilota, posizione> 
    results_by_number = {}
    driver_and_constructor = {}
    for result in race_results.get('Results', []):
        position = result.get('position')
        position_text = result.get('positionText')
        driver_num = int(result['Driver']['permanentNumber'])
        constructor_name = result['Constructor']['constructorId']
        constructor_id = CONSTRUCTOR_MAPPING.get(constructor_name, -1)
        if position_text == 'R':
            position_value = -10  # Ritiro
            results_by_number[driver_num] = position_value  # Ritiro = -10
        elif position_text == 'W':
            position_value = -1  # Non partito (W)
            results_by_number[driver_num] = position_value   # Non partito (W) = -1
        else:
            position_value = int(position) if position.isdigit() else 0
            results_by_number[driver_num] = position_value
        
        position_list = driver_and_constructor.get(constructor_id, [])
        position_list.append(position_value)
        driver_and_constructor[constructor_id] = position_list
    
    # Punteggi driver
    for driver in drivers:
        position = results_by_number.get(driver['number'], 0)
        points = FantasyF1_POINTS.get(position, 0)
        total_score += points
        print(f"  🏁 Driver ID {driver['id']}: posizione {position} = {points} pts")
        break

    # Punteggi costruttori (esempio semplificato: +10 se il costruttore ha un driver in top 10)
    for constructor in constructors:    
            position_values = driver_and_constructor.get(constructor['id'], [])
            for position in position_values:
                points = FantasyF1_POINTS.get(position, 0) / 2
                print(f"  🏁 Costruttore {constructor['name']} points {points} (position {position})")
                total_score += points

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
        constructors = team.get_constructors()
        
        # Calcolo semplificato per demo: somma dei prezzi (da estendere con veri risultati)
        score = sum(d.get('price', 0) for d in drivers if d)
        score += sum(c.get('price', 0) for c in constructors if c)
        
        # Salva/aggiorna il risultato
        result = TeamResult.query.filter_by(team_id=team.id, gp_id=gp_id).first()
        if not result:
            result = TeamResult(team_id=team.id, user_id=team.user_id, gp_id=gp_id)
            db.session.add(result)
        
        result.points = int(score)
        print(f"Team {team.user.username} (GP {gp_id}): {score} pts")
    
    db.session.commit()
    print("Punteggi salvati nel database")

def run_scoring_job(weekend_id=None):
    """Main job - eseguito ogni domenica sera"""
    with app.app_context():
        print(f"\n{'='*60}")
        print(f"FANTASY F1 SCORING JOB - {datetime.now().isoformat()} - Weekend ID: {weekend_id if weekend_id else 'LAST'}")
        print(f"{'='*60}\n")
        
        # 1. Ottieni i risultati della gara più recente da Ergast
        race_data = get_race(weekend_id)
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

        if weekend_id == 100:
            gp = GrandPrix.query.filter_by(id=1).first() 
            
        if not gp:  # Se è un test, non serve trovare il GP
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
