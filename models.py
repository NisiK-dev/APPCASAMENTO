from app import db
from datetime import datetime

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Admin {self.username}>'

class GuestGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # ex: "Família Silva"
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with guests
    guests = db.relationship('Guest', backref='group', lazy=True)

    def __repr__(self):
        return f'<GuestGroup {self.name}>'

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))  # Número de telefone/WhatsApp
    rsvp_status = db.Column(db.String(20), default='pendente')  # pendente, confirmado, nao_confirmado
    group_id = db.Column(db.Integer, db.ForeignKey('guest_group.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Guest {self.name}>'

class VenueInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    map_link = db.Column(db.Text)  # Link do Google Maps
    description = db.Column(db.Text)
    date = db.Column(db.String(100))
    time = db.Column(db.String(100))
    event_datetime = db.Column(db.DateTime)  # Data e hora precisas do evento
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GiftRegistry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.String(50))  # Armazenado como string para flexibilidade
    store_link = db.Column(db.Text)
    image_filename = db.Column(db.String(255))  # Nome do arquivo de imagem
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GiftRegistry {self.item_name}>'