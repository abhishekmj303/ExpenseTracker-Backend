from datetime import datetime
from dataclasses import dataclass
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    username = db.Column(db.String(80), primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hashed = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(80))
    upi = db.Column(db.String(30))


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), default='Untitled Event', nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_private = db.Column(db.Boolean, default=False, nullable=False)


class EventUser(db.Model):
    __tablename__ = 'event_user'
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), primary_key=True)


class EventTransaction(db.Model):
    __tablename__ = 'event_transaction'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    name = db.Column(db.String(80), default='Untitled', nullable=False)
    category = db.Column(db.String(80), default='General', nullable=False)


class TransactionUser(db.Model):
    __tablename__ = 'transaction_user'
    transaction_id = db.Column(db.Integer, db.ForeignKey('event_transaction.id'), primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), primary_key=True)
    amount = db.Column(db.Float, nullable=False)


@dataclass
class Expense(db.Model):
    __tablename__ = 'expense'
    id: int
    username: str
    other_username: str
    amount: float
    event_id: int
    name: str
    category: str
    date: datetime
    is_private: bool

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    other_username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
    name = db.Column(db.String(80))
    category = db.Column(db.String(80), default='General', nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_private = db.Column(db.Boolean, default=False, nullable=False)
    cleared = db.Column(db.Boolean, default=False, nullable=False)
