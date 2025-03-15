from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import logging

db = SQLAlchemy()

# Allowed constants (moved from main code)
ALLOWED_GROUPS = [
    "EDMR", "EDAR", "CDAR", "CCAR", "DDAR", "DDMR",
    "ICAR", "ICMR", "XGAD", "MVAR", "GVAR", "IVAR", "IFAR"
]
ALLOWED_STATUSES = ["available", "unavailable", "maintenance", "rented"]
ROLES = ["Admin", "Rental Team", "Service Team"]

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Admin, Rental Team, Service Team

class Car(db.Model):
    __tablename__ = 'cars'
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(50), nullable=False)
    car_group = db.Column(db.String(4), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    daily_rate = db.Column(db.Float, nullable=True)
    location = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "model": self.model,
            "car_group": self.car_group,
            "status": self.status,
            "year": self.year,
            "daily_rate": self.daily_rate,
            "location": self.location
        }

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('cars.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="booked")  # e.g. booked, canceled, completed

    car = db.relationship('Car', backref='reservations')

    def to_dict(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "car_id": self.car_id,
            "start_date": str(self.start_date),
            "end_date": str(self.end_date),
            "status": self.status
        }

def seed_admin_user(db):
    """Create default admin user if not exists."""
    from werkzeug.security import generate_password_hash
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        hashed = generate_password_hash('Greg12@^*')
        admin_user = User(username='admin', password_hash=hashed, role='Admin')
        db.session.add(admin_user)
        db.session.commit()
        logging.info("Created default admin user: username='admin', password='Greg12@^*'")
