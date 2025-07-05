import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "wedding-rsvp-secret-key-2025")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///wedding_rsvp.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import models and routes
from models import *
from routes import *

# Create tables and default data
with app.app_context():
    db.create_all()
    
    # Create default admin user if not exists
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(
            username='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin padrão criado: admin/admin123")
    
    # Create default venue info if not exists
    if not VenueInfo.query.first():
        venue = VenueInfo(
            name='Igreja São José',
            address='Rua das Flores, 123 - Centro, São Paulo - SP',
            map_link='https://maps.google.com/?q=Igreja+Sao+Jose+Sao+Paulo',
            description='Cerimônia religiosa seguida de recepção no salão',
            date='15 de Agosto de 2025',
            time='16:00'
        )
        db.session.add(venue)
        db.session.commit()
        print("Informações do local criadas")
    
    # Create sample gift registry if not exists
    if not GiftRegistry.query.first():
        gifts = [
            GiftRegistry(
                item_name='Jogo de Panelas',
                description='Conjunto com 5 panelas antiaderentes',
                price='R$ 299,00',
                store_link='https://exemplo.com/panelas'
            ),
            GiftRegistry(
                item_name='Liquidificador',
                description='Liquidificador de alta potência',
                price='R$ 189,00',
                store_link='https://exemplo.com/liquidificador'
            ),
            GiftRegistry(
                item_name='Jogo de Cama',
                description='Jogo de cama casal 100% algodão',
                price='R$ 149,00',
                store_link='https://exemplo.com/jogo-cama'
            )
        ]
        for gift in gifts:
            db.session.add(gift)
        db.session.commit()
        print("Lista de presentes criada")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)