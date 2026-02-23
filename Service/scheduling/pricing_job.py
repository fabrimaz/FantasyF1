import datetime

from models import Constructor, Driver, GrandPrix
from .api_data_extraction import get_race

def update_pricing(weekend_id):
    print(f"Updating pricing for weekend_id: {weekend_id}")

    # race_data = get_race(weekend_id)
    # if not race_data:
    #     message ="❌ Job abortito: nessun dato di gara disponibile"
    #     print(message)
    #     return message
        
    # # 2. Trova il GP corrispondente nel nostro DB
    # # Ergast usa formato YYYY-MM-DD, il nostro DB ha datetime
    # race_date_str = race_data.get('date')
    # gp = GrandPrix.query.filter(
    #     GrandPrix.date >= datetime.fromisoformat(race_date_str),
    #     GrandPrix.date < datetime.fromisoformat(race_date_str.replace('-', '') + 'T23:59:59')
    # ).first()

    # if weekend_id == 100:
    #     gp = GrandPrix.query.filter_by(id=1).first() 

    # if not gp:  # Se è un test, non serve trovare il GP
    #     message =f"❌ Nessun GP trovato per la data {race_date_str}"
    #     print(message)
    #     return message

    # match_message = f"🎯 Matched GP: {gp.name} (ID {gp.id})"
    # print(match_message)
    
    # update_driver_prices(race_data)
    # update_constructor_prices(weekend_id)

def update_driver_prices(race_data):
    print(f"Updating driver prices")

    drivers = Driver.query.all()
    for driver in drivers:
        print(f"Updating price for driver: {driver.name}")



def update_constructor_prices(weekend_id):
    print(f"Updating  constructor prices")
    constructors = Constructor.query.all()

    for constructor in constructors:
        print(f"Updating price for constructor: {constructor.name}")
        