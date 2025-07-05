import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "wedding-rsvp-secret-key-2025")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///wedding_rsvp.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Create default admin user if it doesn't exist
    from models import Admin, VenueInfo, GiftRegistry
    from werkzeug.security import generate_password_hash
    
    if not Admin.query.first():
        admin = Admin(
            username='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Default admin user created - username: admin, password: admin123")
    
    # Create default venue info if it doesn't exist
    if not VenueInfo.query.first():
        venue = VenueInfo(
            name='Igreja São José',
            address='Rua das Flores, 123, Centro, São Paulo - SP',
            map_link='https://maps.google.com/?q=Igreja+São+José+SP',
            description='Cerimônia religiosa seguida de recepção no salão anexo',
            date='15 de dezembro de 2025',
            time='16:00'
        )
        db.session.add(venue)
        db.session.commit()
        logging.info("Default venue info created")
    
    # Create default gift registry items if they don't exist
    if not GiftRegistry.query.first():
        gifts = [
            GiftRegistry(
                item_name='Jogo de Panelas',
                description='Conjunto completo de panelas antiaderentes',
                price='R$ 299,00',
                store_link='https://exemplo.com/panelas'
            ),
            GiftRegistry(
                item_name='Jogo de Cama Casal',
                description='Jogo de cama 100% algodão, king size',
                price='R$ 180,00',
                store_link='https://exemplo.com/jogo-cama'
            ),
            GiftRegistry(
                item_name='Micro-ondas',
                description='Micro-ondas 30 litros com grill',
                price='R$ 450,00',
                store_link='https://exemplo.com/microondas'
            )
        ]
        for gift in gifts:
            db.session.add(gift)
        db.session.commit()
        logging.info("Default gift registry items created")

# Import routes after app initialization
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
