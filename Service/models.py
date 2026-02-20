from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='Player', nullable=False)  # 'Player' or 'Administrator'
    teams = db.relationship('Team', backref='user', lazy=True, cascade='all, delete-orphan')
    league_memberships = db.relationship('LeagueMembership', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role
        }

class GrandPrix(db.Model):
    __tablename__ = 'grand_prix'
    
    id = db.Column(db.Integer, primary_key=True)
    round_num = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    circuit = db.Column(db.String(120), nullable=False)
    fp1_start = db.Column(db.DateTime, nullable=True)
    lock_date = db.Column(db.DateTime, nullable=True)
    teams = db.relationship('Team', backref='grand_prix', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'round': self.round_num,
            'name': self.name,
            'date': self.date.isoformat(),
            'circuit': self.circuit,
            'fp1_start': self.fp1_start.isoformat() if self.fp1_start else None,
            'lock_date': self.lock_date.isoformat() if self.lock_date else None,
            'status': self.get_status()
        }
    
    def get_status(self):
        """Determina lo status del GP usando la data fittizia del gioco"""
        game_date = GameState.get_game_date()
        gp_date = self.date
        gp_lock = self.lock_date
        
        # Se la gara è passata
        if game_date >= gp_date:
            return 'past'
        
        # Se siamo nel periodo di gara (tra lock e race date)
        elif gp_lock and game_date >= gp_lock and game_date < gp_date:
            return 'started'
        # Se siamo PRIMA del lock_date: solo se dentro 14 giorni dalla race è 'current'
        # Altrimenti è 'future' (non ancora attivato)
        elif gp_lock and game_date < gp_lock:
            days_until_lock = (gp_lock - game_date).days
            if days_until_lock <= 14:  # Entro 14 giorni dal lock è 'current'
                return 'current'
            else:
                return 'future'
        else:
            return 'future'

class Driver(db.Model):
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    team = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    points = db.Column(db.Integer, default=0)
    color = db.Column(db.String(7), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'num': self.number,
            'name': self.name,
            'team': self.team,
            'price': self.price,
            'pts': self.points,
            'color': self.color
        }

class Constructor(db.Model):
    __tablename__ = 'constructors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    points = db.Column(db.Integer, default=0)
    color = db.Column(db.String(7), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'pts': self.points,
            'color': self.color
        }

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gp_id = db.Column(db.Integer, db.ForeignKey('grand_prix.id'), nullable=False)
    drivers_json = db.Column(db.Text, nullable=False, default='[]')
    constructors_json = db.Column(db.Text, nullable=False, default='[]')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def set_drivers(self, drivers):
        self.drivers_json = json.dumps(drivers)
    
    def get_drivers(self):
        return json.loads(self.drivers_json)
    
    def set_constructors(self, constructors):
        self.constructors_json = json.dumps(constructors)
    
    def get_constructors(self):
        return json.loads(self.constructors_json)
    
    def to_dict(self):
        # Team can be edited if we haven't reached the lock_date yet (using game date)
        game_date = GameState.get_game_date()
        can_edit = self.grand_prix.lock_date and self.grand_prix.lock_date > game_date
        return {
            'id': self.id,
            'gp_id': self.gp_id,
            'drivers': self.get_drivers(),
            'constructors': self.get_constructors(),
            'can_edit': can_edit,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class League(db.Model):
    __tablename__ = 'leagues'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    members_count = db.Column(db.Integer, default=0)
    current_round = db.Column(db.String(50), default='Round 1')
    memberships = db.relationship('LeagueMembership', backref='league', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'members': self.members_count,
            'round': self.current_round
        }

class LeagueMembership(db.Model):
    __tablename__ = 'league_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.id'), nullable=False)
    team_name = db.Column(db.String(120), nullable=False)
    points = db.Column(db.Integer, default=0)
    position = db.Column(db.Integer, default=0)
    change = db.Column(db.String(10), default='0')
    joined_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'rank': self.position,
            'name': self.user.username,
            'team': self.team_name,
            'pts': self.points,
            'ch': self.change,
            'me': False
        }
class TeamResult(db.Model):
    __tablename__ = 'team_results'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gp_id = db.Column(db.Integer, db.ForeignKey('grand_prix.id'), nullable=False)
    points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    team = db.relationship('Team', backref='results')
    user = db.relationship('User', backref='team_results')
    grand_prix = db.relationship('GrandPrix', backref='team_results')
    
    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'user_id': self.user_id,
            'gp_id': self.gp_id,
            'points': self.points,
            'username': self.user.username
        }

class GameState(db.Model):
    __tablename__ = 'game_state'
    
    id = db.Column(db.Integer, primary_key=True)
    current_date = db.Column(db.DateTime, nullable=False)  # Data fittizia del gioco
    offset_hours = db.Column(db.Integer, default=0)  # Offset in ore rispetto a UTC
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'current_date': self.current_date.isoformat(),
            'offset_hours': self.offset_hours
        }
    
    @staticmethod
    def get_game_date():
        """Ritorna la data fittizia del gioco"""
        from datetime import datetime
        gs = GameState.query.first()
        if not gs:
            # Se non esiste, creala basata su UTC now
            gs = GameState(current_date=datetime.utcnow())
            db.session.add(gs)
            db.session.commit()
        return gs.current_date