from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import text
from scheduling.pricing_job import update_pricing
from scheduling.scoring_job import run_scoring_job
import migration
from models import db, User, Team, League, LeagueMembership, GrandPrix, TeamResult, GameState, Driver, Constructor
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from auth import generate_token
import os

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') or 'sqlite:///fantasy_f1.db'
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
    
    migration.initialize_f1_data(db)  # Seed leagues, GPs, drivers, constructors

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
        'user': user.to_dict(),
        'token': generate_token(user.id)
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

    output = []
    for tr in teamResults:
        d = dict()
        d['user_id'] = tr.user_id
        d['points'] = tr.points
        d['team'] = next((m.team_name for m in memberships if m.user_id == tr.user_id), None)
        d['team_id'] = Team.query.filter_by(user_id=tr.user_id, gp_id=gp_id).first().id if Team.query.filter_by(user_id=tr.user_id, gp_id=gp_id).first() else None
        output.append(d)
    

    remaining_members = set(member_ids) - set([tr.user_id for tr in teamResults])
    for member_id in remaining_members:
        d = dict()
        d['user_id'] = member_id
        d['points'] = 0
        d['team'] = next((m.team_name for m in memberships if m.user_id == member_id), None)
        d['team_id'] = Team.query.filter_by(user_id=member_id, gp_id=gp_id).first().id if Team.query.filter_by(user_id=member_id, gp_id=gp_id).first() else None
        output.append(d)

    print(output)
    return jsonify({
        'league': league.to_dict(),
        'gp': gp.to_dict(),
        'results': output
    }), 200

#@app.route('/api/teamresult/<int:team_id>/<int:gp_id>', methods=['POST']) #NOT PUBLIC
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

@app.route('/api/processWeekend', methods=['GET'])
@app.route('/api/processWeekend/<int:weekend_id>', methods=['GET'])
def get_weekend_points(weekend_id=None):
    from scheduling.scoring_job import run_scoring_job
    result = 100
    try:
        result = run_scoring_job(weekend_id)
    except Exception as e:
        return jsonify({
            'success': False,
            'weekend_id': weekend_id if weekend_id else 'current',
            'error': str(e)
        }), 500
    
    try:
        result = update_pricing(weekend_id)
    except Exception as e:
        return jsonify({
            'success': False,
            'weekend_id': weekend_id if weekend_id else 'current',
            'error': str(e)
        }), 500
    
    return jsonify({
        'success': True,
        'weekend_id': weekend_id if weekend_id else 'current',
        'result': result
    }), 200

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
