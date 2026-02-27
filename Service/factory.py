from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from models import db
from dotenv import load_dotenv

load_dotenv('secrets.env')

def create_app():
    app = Flask(__name__)
    CORS(app,  resources={r"/api/*": {"origins": "*"}})
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') or 'sqlite:///fantasy_f1.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    db.init_app(app)
    return app