from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, User, Team, League, LeagueMembership
import os
from datetime import datetime

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
        demo_user = User(username='demo', email='demo@f1.com')
        demo_user.set_password('demo123')
        db.session.add(demo_user)
        db.session.commit()
    
    # Seed default leagues
    default_leagues = [
        {'code': 'POLE24', 'name': 'Pole Position League', 'members': 42, 'round': 'Round 14 - Belgium GP'},
        {'code': 'FERRARI', 'name': 'Forza Ferrari', 'members': 8, 'round': 'Round 14 - Belgium GP'},
        {'code': 'AMICI01', 'name': 'Sunday Racers', 'members': 6, 'round': 'Round 14 - Belgium GP'},
    ]
    for league_data in default_leagues:
        if not League.query.filter_by(code=league_data['code']).first():
            league = League(
                code=league_data['code'],
                name=league_data['name'],
                members_count=league_data['members'],
                current_round=league_data['round']
            )
            db.session.add(league)
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
    
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 201

# ============ TEAM ENDPOINTS ============

@app.route('/api/team/<int:user_id>', methods=['GET'])
def get_team(user_id):
    team = Team.query.filter_by(user_id=user_id).first()
    if not team:
        return jsonify({'error': 'Team non trovato'}), 404
    
    return jsonify(team.to_dict()), 200

@app.route('/api/team/<int:user_id>', methods=['POST'])
def save_team(user_id):
    data = request.get_json()
    drivers = data.get('drivers', [])
    constructors = data.get('constructors', [])
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Utente non trovato'}), 404
    
    # Check if team exists
    team = Team.query.filter_by(user_id=user_id).first()
    if not team:
        team = Team(user_id=user_id)
        db.session.add(team)
    
    team.set_drivers(drivers)
    team.set_constructors(constructors)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'team': team.to_dict()
    }), 201

# ============ LEAGUE ENDPOINTS ============

@app.route('/api/leagues', methods=['GET'])
def get_leagues():
    leagues = League.query.all()
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

# ============ REFERENCE DATA ============

@app.route('/api/drivers', methods=['GET'])
def get_drivers():
    drivers = [
        {'id':1,  'num':1,  'name':'Max Verstappen',  'team':'Red Bull',     'price':32.5, 'pts':575, 'color':'#3671C6'},
        {'id':2,  'num':11, 'name':'Sergio Perez',    'team':'Red Bull',     'price':22.0, 'pts':285, 'color':'#3671C6'},
        {'id':3,  'num':44, 'name':'Lewis Hamilton',  'team':'Mercedes',     'price':26.0, 'pts':234, 'color':'#27F4D2'},
        {'id':4,  'num':63, 'name':'George Russell',  'team':'Mercedes',     'price':20.5, 'pts':228, 'color':'#27F4D2'},
        {'id':5,  'num':16, 'name':'Charles Leclerc', 'team':'Ferrari',      'price':25.0, 'pts':306, 'color':'#E8002D'},
        {'id':6,  'num':55, 'name':'Carlos Sainz',    'team':'Ferrari',      'price':21.0, 'pts':290, 'color':'#E8002D'},
        {'id':7,  'num':4,  'name':'Lando Norris',    'team':'McLaren',      'price':24.0, 'pts':374, 'color':'#FF8000'},
        {'id':8,  'num':81, 'name':'Oscar Piastri',   'team':'McLaren',      'price':18.5, 'pts':292, 'color':'#FF8000'},
        {'id':9,  'num':14, 'name':'Fernando Alonso', 'team':'Aston Martin', 'price':17.0, 'pts':206, 'color':'#358C75'},
        {'id':10, 'num':18, 'name':'Lance Stroll',    'team':'Aston Martin', 'price':10.0, 'pts':74,  'color':'#358C75'},
        {'id':11, 'num':10, 'name':'Pierre Gasly',    'team':'Alpine',       'price':10.5, 'pts':62,  'color':'#0093CC'},
        {'id':12, 'num':31, 'name':'Esteban Ocon',    'team':'Alpine',       'price':9.5,  'pts':58,  'color':'#0093CC'},
        {'id':13, 'num':23, 'name':'Alex Albon',      'team':'Williams',     'price':9.0,  'pts':42,  'color':'#64C4FF'},
        {'id':14, 'num':22, 'name':'Yuki Tsunoda',    'team':'RB',           'price':9.5,  'pts':22,  'color':'#6692FF'},
        {'id':15, 'num':27, 'name':'Nico Hulkenberg', 'team':'Haas',         'price':9.0,  'pts':31,  'color':'#B6BABD'},
        {'id':16, 'num':3,  'name':'Daniel Ricciardo','team':'RB',           'price':9.0,  'pts':12,  'color':'#6692FF'},
        {'id':17, 'num':77, 'name':'Valtteri Bottas', 'team':'Sauber',       'price':8.0,  'pts':10,  'color':'#52E252'},
        {'id':18, 'num':24, 'name':'Guanyu Zhou',     'team':'Sauber',       'price':7.5,  'pts':6,   'color':'#52E252'},
        {'id':19, 'num':20, 'name':'Kevin Magnussen', 'team':'Haas',         'price':7.5,  'pts':16,  'color':'#B6BABD'},
        {'id':20, 'num':2,  'name':'Logan Sargeant',  'team':'Williams',     'price':7.0,  'pts':1,   'color':'#64C4FF'},
    ]
    return jsonify(drivers), 200

@app.route('/api/constructors', methods=['GET'])
def get_constructors():
    constructors = [
        {'id':1, 'name':'Red Bull Racing', 'price':28.0, 'pts':860, 'color':'#3671C6'},
        {'id':2, 'name':'Ferrari',         'price':23.0, 'pts':596, 'color':'#E8002D'},
        {'id':3, 'name':'McLaren',         'price':22.0, 'pts':666, 'color':'#FF8000'},
        {'id':4, 'name':'Mercedes',        'price':20.0, 'pts':462, 'color':'#27F4D2'},
        {'id':5, 'name':'Aston Martin',    'price':14.0, 'pts':280, 'color':'#358C75'},
        {'id':6, 'name':'Alpine',          'price':9.0,  'pts':120, 'color':'#0093CC'},
        {'id':7, 'name':'Williams',        'price':8.0,  'pts':43,  'color':'#64C4FF'},
        {'id':8, 'name':'RB',              'price':8.5,  'pts':34,  'color':'#6692FF'},
        {'id':9, 'name':'Haas',            'price':7.5,  'pts':47,  'color':'#B6BABD'},
        {'id':10,'name':'Kick Sauber',     'price':7.0,  'pts':16,  'color':'#52E252'},
    ]
    return jsonify(constructors), 200

# ============ HEALTH CHECK ============

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
