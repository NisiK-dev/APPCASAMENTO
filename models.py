from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class AdminUser(db.Model):
    __tablename__ = 'admin_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Alias para compatibilidade
Admin = AdminUser

class GuestGroup(db.Model):
    __tablename__ = 'guest_group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guests = db.relationship('Guest', backref='group', lazy=True)

class Guest(db.Model):
    __tablename__ = 'guest'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    rsvp_status = db.Column(db.String(20), default='pendente')
    group_id = db.Column(db.Integer, db.ForeignKey('guest_group.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GiftRegistry(db.Model):
    __tablename__ = 'presente'
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.String(50))
    image_url = db.Column(db.String(500))
    image_filename = db.Column(db.String(255))
    pix_key = db.Column(db.String(255))
    pix_link = db.Column(db.String(500))
    credit_card_link = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class VenueInfo(db.Model):
    __tablename__ = 'venue_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    map_link = db.Column(db.String(500))
    description = db.Column(db.Text)
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    event_datetime = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
