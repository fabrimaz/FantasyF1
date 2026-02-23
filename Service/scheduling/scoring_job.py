"""
Fantasy F1 Scoring Job
Calcola i punteggi dei team basandosi sui risultati ufficiali F1 (Ergast API)
Schedulato per girare ogni domenica sera dopo il GP o chiamata da API
"""

from datetime import datetime
import sys

import os

# Aggiungi il parent directory al path per gli import

from .api_data_extraction import get_race
from models import db, Team, TeamResult, GrandPrix, User
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

def calculate_team_score(drivers, constructors, race_results):
    """
    Calcola il punteggio totale di un team basandosi sui driver selezionati
    
    Args:
        team: oggetto Team con i driver selezionati
        race_results: dict con i risultati della gara da Ergast
    
    Returns:
        int: punteggio totale del team
    """
    total_score = 0
    # Crea un dict <pilota, posizione> 
    results_by_number = {}
    driver_and_constructor = {}
    for result in race_results.get('Results', []):
        position = result.get('position')
        position_text = result.get('positionText')
        driver_num = int(result['Driver']['permanentNumber'])
        constructor_name = result['Constructor']['constructorId']
        print(f"  🏁 Risultato: Driver #{driver_num} ({constructor_name}) - posizione {position} (text: {position_text})")
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

    print()
    # Punteggi driver
    for driver in drivers:
        position = results_by_number.get(driver['num'], 0)
        points = FantasyF1_POINTS.get(position, 0)
        total_score += points
        print(f"  🏁 Driver ID {driver['id']}: posizione {position} = {points} pts")

    print(constructors)
    # Punteggi costruttori (esempio semplificato: +10 se il costruttore ha un driver in top 10)
    for constructor in constructors:    
            position_values = driver_and_constructor.get(constructor['id'], [])
            print(position_values)
            for position in position_values:
                points = FantasyF1_POINTS.get(position, 0) / 2
                print(f"  🏁 Costruttore {constructor['name']} points {points} (position {position})")
                total_score += points

    print(f"Punteggio totale team: {total_score} pts")
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
        
        score = calculate_team_score(drivers, constructors, race_data)
        
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
