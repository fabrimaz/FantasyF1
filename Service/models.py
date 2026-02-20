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
            'email': self.email
        }

class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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
        return {
            'id': self.id,
            'drivers': self.get_drivers(),
            'constructors': self.get_constructors(),
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
