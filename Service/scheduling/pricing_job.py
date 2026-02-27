from copyreg import constructor
from datetime import datetime
from models import Constructor, Driver, GrandPrix, Team, DriverPrices, ConstructorPrices, TeamResult
from .api_data_extraction import get_race
from factory import db, create_app

def update_pricing(app, weekend_id):
    print(f"Updating pricing for weekend_id: {weekend_id}")

    with app.app_context():
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
        
        teams_for_weekend = Team.query.filter_by(gp_id=gp.id).all()

        driver_new_prices = update_driver_prices(gp.id, teams_for_weekend, race_data)
        constructors_new_prices = update_constructor_prices(gp.id, teams_for_weekend, race_data)
        save_new_prices_history_table(gp.id, driver_new_prices, constructors_new_prices)
        return {
            'drivers': driver_new_prices,
            'constructors': constructors_new_prices
        }

def update_driver_prices(gp_id, teams_for_weekend, race_data):
    
    print(f"Updating driver prices for weekend_id: {gp_id}")
    learning_rate = 0.1
    total_occurences = 0

    all_drivers = Driver.query.all()
    drivers_occurrence = {driver.number: 0 for driver in all_drivers}
    drivers_new_prices = {driver.number: 0 for driver in all_drivers}
    for team in teams_for_weekend:
        drivers = team.get_drivers()
        print(drivers)
        for driver in drivers:
            driver_number = driver['num']
            if driver_number in drivers_occurrence:
                drivers_occurrence[driver_number] += 1
                total_occurences += 1

    average_occurrence = total_occurences / len(drivers_occurrence) if len(drivers_occurrence) > 0 else 0
    print(f"Total occurrences: {total_occurences}, Average occurrence: {average_occurrence}")
    for driver in all_drivers:
        perc_occurence = (drivers_occurrence[driver.number] - average_occurrence) / average_occurrence if average_occurrence > 0 else 0
        adjusted_price = driver.price * (1 + learning_rate * perc_occurence)
        print(adjusted_price)
        new_price = 0.7 * driver.price + 0.3 * adjusted_price
        drivers_new_prices[driver.number] = round(new_price, 1)
        print(f"- {driver.name}, new price: {new_price}, old price: {driver.price}, occurrence: {drivers_occurrence[driver.number]}")

    return drivers_new_prices

def update_constructor_prices(gp_id, teams_for_weekend, race_data):
    print(f"Updating  constructor prices for gp_id: {gp_id}")
    learning_rate = 0.1
    total_occurences = 0

    all_constructors = Constructor.query.all()
    constructors_occurrence = {constructor.id: 0 for constructor in all_constructors}
    constructors_new_prices = {constructor.id: 0 for constructor in all_constructors}
    for team in teams_for_weekend:
        constructors = team.get_constructors()
        print(constructors)
        for constructor in constructors:
            constructor_id = constructor['id']
            if constructor_id in constructors_occurrence:
                constructors_occurrence[constructor_id] += 1
                total_occurences += 1

    average_occurrence = total_occurences / len(constructors_occurrence) if len(constructors_occurrence) > 0 else 0
    print(f"Total occurrences: {total_occurences}, Average occurrence: {average_occurrence}")
    for constructor in all_constructors:
        perc_occurence = (constructors_occurrence[constructor.id] - average_occurrence) / average_occurrence if average_occurrence > 0 else 0
        adjusted_price = constructor.price * (1 + learning_rate * perc_occurence)
        new_price = 0.7 * constructor.price + 0.3 * adjusted_price
        constructors_new_prices[constructor.id] = round(new_price, 1)
        print(f"- {constructor.name}, new price: {new_price}, old price: {constructor.price}, occurrence: {constructors_occurrence[constructor.id]}")

    return constructors_new_prices

def save_new_prices_default_table(drivers_new_prices, constructors_new_prices):
    for driver_num, new_price in drivers_new_prices.items():
        driver = Driver.query.filter_by(number=driver_num).first()
        if driver:
            driver.price = new_price
            print(f"Updated price for driver {driver.name} to {new_price}")
    
    for constructor_id, new_price in constructors_new_prices.items():
        constructor = Constructor.query.filter_by(id=constructor_id).first()
        if constructor:
            constructor.price = new_price
            print(f"Updated price for constructor {constructor.name} to {new_price}")
    
    db.session.commit()

def save_new_prices_history_table(gp_id, drivers_new_prices, constructors_new_prices):
    
    result = DriverPrices.query.filter_by(gp_id=gp_id).first()
    if not result:
        for driver_num, new_price in drivers_new_prices.items():
            driver_price = DriverPrices(
                driver_id=driver_num,
                price=new_price,
                gp_id=gp_id)
            db.session.add(driver_price)
    
    result = ConstructorPrices.query.filter_by(gp_id=gp_id).first()
    if not result:
        for constructor_id, new_price in constructors_new_prices.items():
            constructor_price = ConstructorPrices(
                constructor_id=constructor_id,
                price=new_price,
                gp_id=gp_id)
            db.session.add(constructor_price)
    
    db.session.commit()


if __name__ == '__main__':
    update_pricing()