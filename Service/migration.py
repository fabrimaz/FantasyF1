
from datetime import datetime
from pydoc import text
from models import Constructor, Driver, GrandPrix, League


def initialize_f1_data(db):
    
    default_leagues = [
        {'id' : 1, 'code': 'POLE24', 'name': 'Pole Position League', 'members': 0, 'round': 'Round 14 - Belgium GP'},
        {'id' : 2, 'code': 'FERRARI', 'name': 'Forza Ferrari', 'members': 0, 'round': 'Round 14 - Belgium GP'},
        {'id' : 3, 'code': 'AMICI01', 'name': 'Sunday Racers', 'members': 0, 'round': 'Round 14 - Belgium GP'},
    ]
    for league_data in default_leagues:
        if not League.query.filter_by(code=league_data['code']).first():
            league = League(
                id=league_data['id'],
                code=league_data['code'],
                name=league_data['name'],
                members_count=league_data['members'],
                current_round=league_data['round']
            )
            db.session.add(league)
    db.session.commit()
    
    if GrandPrix.query.count() == 0:
        # Seed Grand Prix (2026 F1 season) 
        # Clear existing GP data
        GrandPrix.query.delete()
        db.session.execute(text("ALTER SEQUENCE grand_prix_id_seq RESTART WITH 1"))

        gps = [
            # lock_date deve essere PRIMA della gara (sabato qualifiche ore 17:00, o venerdì spa gare sprint ore 18:00)
            {'id': 1, 'round': 1, 'name': 'Bahrain', 'circuit': 'Bahrain International Circuit', 'date': datetime(2026, 3, 1), 'fp1_start': datetime(2026, 2, 27, 10, 0), 'lock_date': datetime(2026, 2, 28, 17, 0)},
            {'id': 2,'round': 2, 'name': 'Saudi Arabia', 'circuit': 'Jeddah Corniche Circuit', 'date': datetime(2026, 3, 8), 'fp1_start': datetime(2026, 3, 6, 10, 0), 'lock_date': datetime(2026, 3, 7, 17, 0)},
            {'id': 3,'round': 3, 'name': 'Australia', 'circuit': 'Albert Park Circuit', 'date': datetime(2026, 3, 22), 'fp1_start': datetime(2026, 3, 20, 19, 0), 'lock_date': datetime(2026, 3, 20, 18, 0)},  # Sprint
            {'id': 4,'round': 4, 'name': 'China', 'circuit': 'Shanghai International Circuit', 'date': datetime(2026, 4, 5), 'fp1_start': datetime(2026, 4, 3, 9, 0), 'lock_date': datetime(2026, 4, 3, 18, 0)},  # Sprint
            {'id': 5,'round': 5, 'name': 'Japan', 'circuit': 'Suzuka International Racing Course', 'date': datetime(2026, 4, 19), 'fp1_start': datetime(2026, 4, 17, 10, 0), 'lock_date': datetime(2026, 4, 18, 17, 0)},
            {'id': 6,'round': 6, 'name': 'Monaco', 'circuit': 'Circuit de Monaco', 'date': datetime(2026, 5, 24), 'fp1_start': datetime(2026, 5, 22, 11, 0), 'lock_date': datetime(2026, 5, 23, 17, 0)},
            {'id': 7,'round': 7, 'name': 'Canada', 'circuit': 'Circuit Gilles Villeneuve', 'date': datetime(2026, 6, 7), 'fp1_start': datetime(2026, 6, 5, 13, 0), 'lock_date': datetime(2026, 6, 6, 17, 0)},
            {'id': 8,'round': 8, 'name': 'Spain', 'circuit': 'Circuit de Barcelona-Catalunya', 'date': datetime(2026, 6, 21), 'fp1_start': datetime(2026, 6, 19, 10, 0), 'lock_date': datetime(2026, 6, 20, 17, 0)},
            {'id': 9,'round': 9, 'name': 'Austria', 'circuit': 'Red Bull Ring', 'date': datetime(2026, 7, 5), 'fp1_start': datetime(2026, 7, 3, 10, 0), 'lock_date': datetime(2026, 7, 4, 17, 0)},
            {'id': 10,'round': 10, 'name': 'Britain', 'circuit': 'Silverstone Circuit', 'date': datetime(2026, 7, 19), 'fp1_start': datetime(2026, 7, 17, 10, 0), 'lock_date': datetime(2026, 7, 18, 17, 0)},
            {'id': 11,'round': 11, 'name': 'Belgium', 'circuit': 'Circuit de Spa-Francorchamps', 'date': datetime(2026, 8, 2), 'fp1_start': datetime(2026, 7, 31, 10, 0), 'lock_date': datetime(2026, 8, 1, 17, 0)},
            {'id': 12,'round': 12, 'name': 'Netherlands', 'circuit': 'Zandvoort Circuit', 'date': datetime(2026, 8, 30), 'fp1_start': datetime(2026, 8, 28, 11, 0), 'lock_date': datetime(2026, 8, 29, 17, 0)},
            {'id': 13,'round': 13, 'name': 'Italy', 'circuit': 'Autodromo Nazionale di Monza', 'date': datetime(2026, 9, 6), 'fp1_start': datetime(2026, 9, 4, 10, 0), 'lock_date': datetime(2026, 9, 5, 17, 0)},
            {'id': 14,'round': 14, 'name': 'Azerbaijan', 'circuit': 'Baku City Circuit', 'date': datetime(2026, 9, 20), 'fp1_start': datetime(2026, 9, 18, 9, 0), 'lock_date': datetime(2026, 9, 19, 17, 0)},
            {'id': 15,'round': 15, 'name': 'Singapore', 'circuit': 'Marina Bay Street Circuit', 'date': datetime(2026, 10, 4), 'fp1_start': datetime(2026, 10, 2, 10, 0), 'lock_date': datetime(2026, 10, 3, 17, 0)},
            {'id': 16,'round': 16, 'name': 'USA', 'circuit': 'Circuit of the Americas', 'date': datetime(2026, 10, 18), 'fp1_start': datetime(2026, 10, 16, 12, 0), 'lock_date': datetime(2026, 10, 16, 18, 0)},  # Sprint
            {'id': 17,'round': 17, 'name': 'Mexico', 'circuit': 'Autódromo Hermanos Rodríguez', 'date': datetime(2026, 10, 25), 'fp1_start': datetime(2026, 10, 23, 11, 0), 'lock_date': datetime(2026, 10, 24, 17, 0)},
            {'id': 18,'round': 18, 'name': 'Brazil', 'circuit': 'Autódromo José Carlos Pace', 'date': datetime(2026, 11, 1), 'fp1_start': datetime(2026, 10, 30, 12, 0), 'lock_date': datetime(2026, 10, 30, 18, 0)},  # Sprint
            {'id': 19,'round': 19, 'name': 'Abu Dhabi', 'circuit': 'Yas Marina Circuit', 'date': datetime(2026, 11, 29), 'fp1_start': datetime(2026, 11, 27, 8, 0), 'lock_date': datetime(2026, 11, 28, 17, 0)},
        ]
        for gp_data in gps:
            gp = GrandPrix(
                id=gp_data['id'],
                round_num=gp_data['round'],
                name=gp_data['name'],
                circuit=gp_data['circuit'],
                date=gp_data['date'],
                fp1_start=gp_data['fp1_start'],
                lock_date=gp_data['lock_date']
            )
            db.session.add(gp)
        db.session.commit()
    
    if Driver.query.count() == 0:
        # Seed Drivers (griglia 2026)
        Driver.query.delete()
        db.session.execute(text("ALTER SEQUENCE drivers_id_seq RESTART WITH 1"))

        drivers_data = [
            {'num':3,  'name':'Max Verstappen',     'team':'Red Bull Racing',  'price':25.0, 'pts':0, 'color':'#0600FF'},
            {'num':6,  'name':'Isack Hadjar',       'team':'Red Bull Racing',  'price':9.0,  'pts':0, 'color':'#0600FF'},
            {'num':1,  'name':'Lando Norris',       'team':'McLaren',          'price':23.0, 'pts':0, 'color':'#FF8700'},
            {'num':81, 'name':'Oscar Piastri',      'team':'McLaren',          'price':22.0, 'pts':0, 'color':'#FF8700'},
            {'num':16, 'name':'Charles Leclerc',    'team':'Ferrari',          'price':24.0, 'pts':0, 'color':'#DC0000'},
            {'num':44, 'name':'Lewis Hamilton',     'team':'Ferrari',          'price':24.0, 'pts':0, 'color':'#DC0000'},
            {'num':12, 'name':'Kimi Antonelli',     'team':'Mercedes',         'price':15.0, 'pts':0, 'color':'#00D2BE'},
            {'num':63, 'name':'George Russell',     'team':'Mercedes',         'price':20.0, 'pts':0, 'color':'#00D2BE'},
            {'num':14, 'name':'Fernando Alonso',    'team':'Aston Martin',     'price':21.0, 'pts':0, 'color':'#006341'},
            {'num':18, 'name':'Lance Stroll',       'team':'Aston Martin',     'price':18.0, 'pts':0, 'color':'#006341'},
            {'num':23, 'name':'Alexander Albon',    'team':'Williams',         'price':17.0, 'pts':0, 'color':'#003262'},
            {'num':55, 'name':'Carlos Sainz Jr.',   'team':'Williams',         'price':21.0, 'pts':0, 'color':'#003262'},
            {'num':5,  'name':'Gabriel Bortoleto',  'team':'Audi',             'price':16.0, 'pts':0, 'color':'#E5001B'},
            {'num':27, 'name':'Nico Hülkenberg',    'team':'Audi',             'price':19.0, 'pts':0, 'color':'#E5001B'},
            {'num':11, 'name':'Sergio Pérez',       'team':'Cadillac',         'price':18.0, 'pts':0, 'color':'#003478'},
            {'num':77, 'name':'Valtteri Bottas',    'team':'Cadillac',         'price':13.0, 'pts':0, 'color':'#003478'},
            {'num':31, 'name':'Esteban Ocon',       'team':'Haas',             'price':12.0, 'pts':0, 'color':'#C8102E'},
            {'num':87, 'name':'Oliver Bearman',     'team':'Haas',             'price':8.0, 'pts':0, 'color':'#C8102E'},
            {'num':10, 'name':'Pierre Gasly',       'team':'Alpine',           'price':5.0, 'pts':0, 'color':'#0082FA'},
            {'num':43, 'name':'Franco Colapinto',   'team':'Alpine',           'price':5.0, 'pts':0, 'color':'#0082FA'},
        ]
        for driver_data in drivers_data:
            driver = Driver(
                id=driver_data['num'],  # Usa il numero del pilota come ID
                number=driver_data['num'],
                name=driver_data['name'],
                team=driver_data['team'],
                price=driver_data['price'],
                points=driver_data['pts'],
                color=driver_data['color']
            )
            db.session.add(driver)
        db.session.commit()
    
    if Constructor.query.count() == 0:
        # Seed Constructors (griglia 2026)
        Constructor.query.delete()
        constructors_data = [
            {'name':'Red Bull Racing',  'price':34.0, 'pts':0, 'color':'#0600FF'},
            {'name':'McLaren',          'price':45.0, 'pts':0, 'color':'#FF8700'},
            {'name':'Ferrari',          'price':48.0, 'pts':0, 'color':'#DC0000'},
            {'name':'Mercedes',         'price':35.0, 'pts':0, 'color':'#00D2BE'},
            {'name':'Aston Martin',     'price':39.0, 'pts':0, 'color':'#006341'},
            {'name':'Williams',         'price':38.0, 'pts':0, 'color':'#003262'},
            {'name':'Audi',             'price':35.0, 'pts':0, 'color':'#E5001B'},
            {'name':'Cadillac',         'price':31.0, 'pts':0, 'color':'#003478'},
            {'name':'Haas',             'price':26.0, 'pts':0, 'color':'#C8102E'},
            {'name':'Alpine',           'price':27.0, 'pts':0, 'color':'#0082FA'},
        ]
        for constructor_data in constructors_data:
            constructor = Constructor(
                name=constructor_data['name'],
                price=constructor_data['price'],
                points=constructor_data['pts'],
                color=constructor_data['color']
            )
            db.session.add(constructor)
        db.session.commit()

    return