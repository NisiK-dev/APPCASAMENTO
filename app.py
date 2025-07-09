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
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
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

    # Criar grupos de exemplo se não existirem
    if GuestGroup.query.count() == 0:
        groups = [
            GuestGroup(name='Família Silva', description='Parentes do lado da noiva'),
            GuestGroup(name='Família Santos', description='Parentes do lado do noivo'),
            GuestGroup(name='Amigos da Faculdade', description='Turma da universidade')
        ]
        for group in groups:
            db.session.add(group)
        db.session.commit()
        print("Grupos de exemplo criados")

    # Criar convidados de exemplo se não existirem
    if Guest.query.count() == 0:
        # Obter os grupos criados
        familia_silva = GuestGroup.query.filter_by(name='Família Silva').first()
        familia_santos = GuestGroup.query.filter_by(name='Família Santos').first()
        amigos_faculdade = GuestGroup.query.filter_by(name='Amigos da Faculdade').first()
        
        guests = [
            # Família Silva
            Guest(name='João Silva', phone='+5511999999999', group_id=familia_silva.id),
            Guest(name='Maria Silva', phone='+5511888888888', group_id=familia_silva.id),
            Guest(name='Pedro Silva', phone='+5511777777777', group_id=familia_silva.id),
            
            # Família Santos
            Guest(name='Ana Santos', phone='+5511666666666', group_id=familia_santos.id),
            Guest(name='Carlos Santos', phone='+5511555555555', group_id=familia_santos.id),
            Guest(name='Lucia Santos', phone='+5511444444444', group_id=familia_santos.id),
            
            # Amigos da Faculdade
            Guest(name='Rafael Oliveira', phone='+5511333333333', group_id=amigos_faculdade.id),
            Guest(name='Marina Costa', phone='+5511222222222', group_id=amigos_faculdade.id),
            Guest(name='Bruno Ferreira', phone='+5511111111111', group_id=amigos_faculdade.id),
            
            # Convidados individuais (sem grupo)
            Guest(name='Roberto Lima', phone='+5511000000000'),
            Guest(name='Fernanda Almeida', phone='+5511999000000')
        ]
        
        for guest in guests:
            db.session.add(guest)
        db.session.commit()
        print("Convidados de exemplo criados")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)