from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, User, Team, League, LeagueMembership, GrandPrix, TeamResult, GameState, Driver, Constructor
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fantasy_f1.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

# Initialize extensions
db.init_app(app)
CORS(app)

# Create database tables
with app.app_context():
    db.create_all()
    
    # Seed demo user if doesn't exist
    if not User.query.filter_by(email='demo@f1.com').first():
        demo_user = User(username='demo', email='demo@f1.com', role='Player')
        demo_user.set_password('demo123')
        db.session.add(demo_user)
        db.session.commit()
    
    # Seed admin user if doesn't exist
    if not User.query.filter_by(email='admin@f1.com').first():
        admin_user = User(username='admin', email='admin@f1.com', role='Administrator')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
    
    # Initialize GameState if doesn't exist
    if not GameState.query.first():
        game_state = GameState(current_date=datetime.utcnow())
        db.session.add(game_state)
        db.session.commit()
    
    # Seed default leagues
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
    
    # Seed Grand Prix (2026 F1 season)
    # Clear existing GP data
    GrandPrix.query.delete()
    
    gps = [
        # lock_date deve essere PRIMA della gara (sabato qualifiche ore 17:00, o venerdì spa gare sprint ore 18:00)
        {'round': 1, 'name': 'Bahrain', 'circuit': 'Bahrain International Circuit', 'date': datetime(2026, 3, 1), 'fp1_start': datetime(2026, 2, 27, 10, 0), 'lock_date': datetime(2026, 2, 28, 17, 0)},
        {'round': 2, 'name': 'Saudi Arabia', 'circuit': 'Jeddah Corniche Circuit', 'date': datetime(2026, 3, 8), 'fp1_start': datetime(2026, 3, 6, 10, 0), 'lock_date': datetime(2026, 3, 7, 17, 0)},
        {'round': 3, 'name': 'Australia', 'circuit': 'Albert Park Circuit', 'date': datetime(2026, 3, 22), 'fp1_start': datetime(2026, 3, 20, 19, 0), 'lock_date': datetime(2026, 3, 20, 18, 0)},  # Sprint
        {'round': 4, 'name': 'China', 'circuit': 'Shanghai International Circuit', 'date': datetime(2026, 4, 5), 'fp1_start': datetime(2026, 4, 3, 9, 0), 'lock_date': datetime(2026, 4, 3, 18, 0)},  # Sprint
        {'round': 5, 'name': 'Japan', 'circuit': 'Suzuka International Racing Course', 'date': datetime(2026, 4, 19), 'fp1_start': datetime(2026, 4, 17, 10, 0), 'lock_date': datetime(2026, 4, 18, 17, 0)},
        {'round': 6, 'name': 'Monaco', 'circuit': 'Circuit de Monaco', 'date': datetime(2026, 5, 24), 'fp1_start': datetime(2026, 5, 22, 11, 0), 'lock_date': datetime(2026, 5, 23, 17, 0)},
        {'round': 7, 'name': 'Canada', 'circuit': 'Circuit Gilles Villeneuve', 'date': datetime(2026, 6, 7), 'fp1_start': datetime(2026, 6, 5, 13, 0), 'lock_date': datetime(2026, 6, 6, 17, 0)},
        {'round': 8, 'name': 'Spain', 'circuit': 'Circuit de Barcelona-Catalunya', 'date': datetime(2026, 6, 21), 'fp1_start': datetime(2026, 6, 19, 10, 0), 'lock_date': datetime(2026, 6, 20, 17, 0)},
        {'round': 9, 'name': 'Austria', 'circuit': 'Red Bull Ring', 'date': datetime(2026, 7, 5), 'fp1_start': datetime(2026, 7, 3, 10, 0), 'lock_date': datetime(2026, 7, 4, 17, 0)},
        {'round': 10, 'name': 'Britain', 'circuit': 'Silverstone Circuit', 'date': datetime(2026, 7, 19), 'fp1_start': datetime(2026, 7, 17, 10, 0), 'lock_date': datetime(2026, 7, 18, 17, 0)},
        {'round': 11, 'name': 'Belgium', 'circuit': 'Circuit de Spa-Francorchamps', 'date': datetime(2026, 8, 2), 'fp1_start': datetime(2026, 7, 31, 10, 0), 'lock_date': datetime(2026, 8, 1, 17, 0)},
        {'round': 12, 'name': 'Netherlands', 'circuit': 'Zandvoort Circuit', 'date': datetime(2026, 8, 30), 'fp1_start': datetime(2026, 8, 28, 11, 0), 'lock_date': datetime(2026, 8, 29, 17, 0)},
        {'round': 13, 'name': 'Italy', 'circuit': 'Autodromo Nazionale di Monza', 'date': datetime(2026, 9, 6), 'fp1_start': datetime(2026, 9, 4, 10, 0), 'lock_date': datetime(2026, 9, 5, 17, 0)},
        {'round': 14, 'name': 'Azerbaijan', 'circuit': 'Baku City Circuit', 'date': datetime(2026, 9, 20), 'fp1_start': datetime(2026, 9, 18, 9, 0), 'lock_date': datetime(2026, 9, 19, 17, 0)},
        {'round': 15, 'name': 'Singapore', 'circuit': 'Marina Bay Street Circuit', 'date': datetime(2026, 10, 4), 'fp1_start': datetime(2026, 10, 2, 10, 0), 'lock_date': datetime(2026, 10, 3, 17, 0)},
        {'round': 16, 'name': 'USA', 'circuit': 'Circuit of the Americas', 'date': datetime(2026, 10, 18), 'fp1_start': datetime(2026, 10, 16, 12, 0), 'lock_date': datetime(2026, 10, 16, 18, 0)},  # Sprint
        {'round': 17, 'name': 'Mexico', 'circuit': 'Autódromo Hermanos Rodríguez', 'date': datetime(2026, 10, 25), 'fp1_start': datetime(2026, 10, 23, 11, 0), 'lock_date': datetime(2026, 10, 24, 17, 0)},
        {'round': 18, 'name': 'Brazil', 'circuit': 'Autódromo José Carlos Pace', 'date': datetime(2026, 11, 1), 'fp1_start': datetime(2026, 10, 30, 12, 0), 'lock_date': datetime(2026, 10, 30, 18, 0)},  # Sprint
        {'round': 19, 'name': 'Abu Dhabi', 'circuit': 'Yas Marina Circuit', 'date': datetime(2026, 11, 29), 'fp1_start': datetime(2026, 11, 27, 8, 0), 'lock_date': datetime(2026, 11, 28, 17, 0)},
    ]
    for gp_data in gps:
        gp = GrandPrix(
            round_num=gp_data['round'],
            name=gp_data['name'],
            circuit=gp_data['circuit'],
            date=gp_data['date'],
            fp1_start=gp_data['fp1_start'],
            lock_date=gp_data['lock_date']
        )
        db.session.add(gp)
    db.session.commit()
    
    # Seed Drivers (griglia 2026)
    Driver.query.delete()
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
            number=driver_data['num'],
            name=driver_data['name'],
            team=driver_data['team'],
            price=driver_data['price'],
            points=driver_data['pts'],
            color=driver_data['color']
        )
        db.session.add(driver)
    db.session.commit()
    
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

# ============ AUTH ENDPOINTS ============

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'error': 'Email e password obbligatori'}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Credenziali non valide'}), 401
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 200

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': 'Compila tutti i campi'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email gia in uso'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username gia in uso'}), 400
    
    user = User(username=username, email=email, role='Player')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 201


# def send_login_email(to_email, username):
#     message = Mail(
#         from_email='tuaemail@gmail.com',  # quella con cui ti sei registrato su SendGrid
#         to_emails=to_email,
#         subject='Nuovo accesso a FantasyF1',
#         html_content=f'<p>Ciao {username}, hai effettuato un accesso.</p>'
#     )
#     sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
#     sg.send(message)

# ============ GRAND PRIX ENDPOINTS ============

@app.route('/api/grandprix', methods=['GET'])
def get_grandprix():
    gps = GrandPrix.query.order_by(GrandPrix.round_num).all()
    return jsonify([gp.to_dict() for gp in gps]), 200

@app.route('/api/grandprix/<int:gp_id>', methods=['GET'])
def get_gp_detail(gp_id):
    gp = GrandPrix.query.get(gp_id)
    if not gp:
        return jsonify({'error': 'Grand Prix non trovato'}), 404
    return jsonify(gp.to_dict()), 200

# ============ TEAM ENDPOINTS ============

@app.route('/api/team/<int:user_id>/<int:gp_id>', methods=['GET'])
def get_team(user_id, gp_id):
    team = Team.query.filter_by(user_id=user_id, gp_id=gp_id).first()
    if not team:
        # Return empty team if it doesn't exist yet
        gp = GrandPrix.query.get(gp_id)
        if not gp:
            return jsonify({'error': 'Grand Prix non trovato'}), 404
        return jsonify({
            'id': None,
            'gp_id': gp_id,
            'drivers': [],
            'constructors': [],
            'can_edit': gp.get_status() == 'current',
            'created_at': None
        }), 200
    
    return jsonify(team.to_dict()), 200

@app.route('/api/team/<int:user_id>/<int:gp_id>', methods=['POST'])
def save_team(user_id, gp_id):
    data = request.get_json()
    drivers = data.get('drivers', [])
    constructors = data.get('constructors', [])
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Utente non trovato'}), 404
    
    gp = GrandPrix.query.get(gp_id)
    if not gp:
        return jsonify({'error': 'Grand Prix non trovato'}), 404
    
    # Check if GP is past (read-only)
    if gp.get_status() == 'past':
        return jsonify({'error': 'Non puoi modificare team per GP passati'}), 403
    
    # Check if team exists
    team = Team.query.filter_by(user_id=user_id, gp_id=gp_id).first()
    if not team:
        team = Team(user_id=user_id, gp_id=gp_id)
        db.session.add(team)
    
    team.set_drivers(drivers)
    team.set_constructors(constructors)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'team': team.to_dict()
    }), 201

@app.route('/api/user/<int:user_id>/teams', methods=['GET'])
def get_user_teams(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Utente non trovato'}), 404
    
    teams = Team.query.filter_by(user_id=user_id).all()
    return jsonify([team.to_dict() for team in teams]), 200

# ============ LEAGUE ENDPOINTS ============

@app.route('/api/leagues', methods=['GET'])
def get_leagues():
    leagues = League.query.all()
    print('Fetched leagues:', [l.to_dict() for l in leagues])
    return jsonify([league.to_dict() for league in leagues]), 200

@app.route('/api/leagues/<code>', methods=['GET'])
def get_league(code):
    league = League.query.filter_by(code=code).first()
    if not league:
        return jsonify({'error': 'Lega non trovata'}), 404
    
    return jsonify(league.to_dict()), 200

@app.route('/api/leagues/join/<int:user_id>/<code>', methods=['POST'])
def join_league(user_id, code):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Utente non trovato'}), 404
    
    league = League.query.filter_by(code=code).first()
    if not league:
        return jsonify({'error': 'Codice lega non valido'}), 404
    
    # Check if already member
    existing = LeagueMembership.query.filter_by(
        user_id=user_id,
        league_id=league.id
    ).first()
    if existing:
        return jsonify({'error': 'Sei gia in questa lega'}), 400
    
    # Add membership
    membership = LeagueMembership(
        user_id=user_id,
        league_id=league.id,
        team_name=f'{user.username}\'s Team'
    )
    league.members_count += 1
    db.session.add(membership)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'league': league.to_dict()
    }), 201

@app.route('/api/leagues/user/<int:user_id>', methods=['GET'])
def get_user_leagues(user_id):
    memberships = LeagueMembership.query.filter_by(user_id=user_id).all()
    leagues = [membership.league.to_dict() for membership in memberships]
    return jsonify(leagues), 200

@app.route('/api/leaderboard/<int:league_id>', methods=['GET'])
def get_leaderboard(league_id):
    league = League.query.get(league_id)
    if not league:
        return jsonify({'error': 'Lega non trovata'}), 404
    
    memberships = LeagueMembership.query.filter_by(league_id=league_id).all()
    leaderboard = [membership.to_dict() for membership in memberships]
    
    return jsonify({
        'league': league.to_dict(),
        'leaderboard': leaderboard
    }), 200

@app.route('/api/league/<int:league_id>/gp/<int:gp_id>/results', methods=['GET'])
def get_gp_results(league_id, gp_id):
    league = League.query.get(league_id)
    if not league:
        return jsonify({'error': 'Lega non trovata'}), 404
    
    gp = GrandPrix.query.get(gp_id)
    if not gp:
        return jsonify({'error': 'Grand Prix non trovato'}), 404
    
    # Get all members of the league
    memberships = LeagueMembership.query.filter_by(league_id=league_id).all()
    member_ids = [m.user_id for m in memberships]
    
    # Get team results for this GP from league members
    teamResults = TeamResult.query.filter(
        TeamResult.gp_id == gp_id,
        TeamResult.user_id.in_(member_ids)
    ).order_by(TeamResult.points.desc()).all()

    remaining_members = set(member_ids) - set([tr.user_id for tr in teamResults])
    for mid in remaining_members:
        d = dict()
        d['user_id'] = mid
        d['points'] = 0
        d['team'] = next((m.team_name for m in memberships if m.user_id == mid), None)
        teamResults.append(d)
    
    return jsonify({
        'league': league.to_dict(),
        'gp': gp.to_dict(),
        'results': [r for r in teamResults]
    }), 200

@app.route('/api/teamresult/<int:team_id>/<int:gp_id>', methods=['POST'])
def save_team_result(team_id, gp_id):
    data = request.get_json()
    points = data.get('points', 0)
    
    gp = GrandPrix.query.get(gp_id)
    if not gp:
        return jsonify({'error': 'Grand Prix non trovato'}), 404
    
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'error': 'Team non trovato'}), 404
    
    # Check if result already exists
    result = TeamResult.query.filter_by(team_id=team_id, gp_id=gp_id).first()
    if not result:
        result = TeamResult(team_id=team_id, user_id=team.user_id, gp_id=gp_id)
        db.session.add(result)
    
    result.points = points
    db.session.commit()
    
    return jsonify({
        'success': True,
        'result': result.to_dict()
    }), 201

# ============ JOB SCHEDULE ============
# Endpoint deprecated - scoring job no longer used

# @app.route('/api/weekendPoints', methods=['GET'])
# def get_weekend_points():
#     result = 100
#     return jsonify({
#         'success': True,
#         'result': result
#     }), 200

# ============ REFERENCE DATA ============

@app.route('/api/drivers', methods=['GET'])
def get_drivers():
    drivers = Driver.query.all()
    return jsonify([driver.to_dict() for driver in drivers]), 200

@app.route('/api/constructors', methods=['GET'])
def get_constructors():
    constructors = Constructor.query.all()
    return jsonify([constructor.to_dict() for constructor in constructors]), 200

# ============ ADMIN ENDPOINTS ============

@app.route('/api/game/state', methods=['GET'])
def get_game_state():
    """Ritorna lo stato del gioco (data fittizia)"""
    game_state = GameState.query.first()
    if not game_state:
        return jsonify({'error': 'Game state non trovato'}), 404
    return jsonify(game_state.to_dict()), 200

@app.route('/api/game/state', methods=['POST'])
def update_game_state():
    """Aggiorna la data fittizia del gioco (solo admin)"""
    data = request.get_json()
    
    # Verifica admin
    user_id = data.get('admin_id')
    if not user_id:
        return jsonify({'error': 'Admin ID richiesto'}), 400
    
    admin = User.query.get(user_id)
    if not admin or admin.role != 'Administrator':
        return jsonify({'error': 'Solo admin può modificare la data'}), 403
    
    # Aggiorna data
    new_date = data.get('current_date')
    if not new_date:
        return jsonify({'error': 'current_date richiesto'}), 400
    
    try:
        # Prova il parsing ISO
        game_date = datetime.fromisoformat(new_date.replace('Z', '+00:00'))
    except:
        return jsonify({'error': 'Formato data non valido. Usa ISO format (es. 2026-03-15T10:00:00)'}), 400
    
    game_state = GameState.query.first()
    if not game_state:
        game_state = GameState(current_date=game_date)
        db.session.add(game_state)
    else:
        game_state.current_date = game_date
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'game_state': game_state.to_dict()
    }), 200

@app.route('/api/game/state/reset', methods=['POST'])
def reset_game_state():
    """Resetta la data fittizia a now con offset 0 (solo admin)"""
    data = request.get_json()
    
    # Verifica admin
    user_id = data.get('admin_id')
    if not user_id:
        return jsonify({'error': 'Admin ID richiesto'}), 400
    
    admin = User.query.get(user_id)
    if not admin or admin.role != 'Administrator':
        return jsonify({'error': 'Solo admin può resettare la data'}), 403
    
    game_state = GameState.query.first()
    if not game_state:
        game_state = GameState(current_date=datetime.utcnow(), offset_hours=0)
        db.session.add(game_state)
    else:
        game_state.current_date = datetime.utcnow()
        game_state.offset_hours = 0
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'game_state': game_state.to_dict()
    }), 200

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
