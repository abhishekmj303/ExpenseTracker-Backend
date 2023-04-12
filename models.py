from datetime import datetime
from dataclasses import dataclass
from flask_sqlalchemy import SQLAlchemy
# from flask_praetorian import SQLAlchemyUserMixin

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(80))
    upi = db.Column(db.String(30))
    date_joined = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_confirm = db.Column(db.Boolean, default=False, server_default="false")
    is_active = db.Column(db.Boolean, default=True, server_default="true")

    events = db.relationship('Event', secondary='event_user', back_populates='users')
    transactions = db.relationship('Transaction', secondary='transaction_user', back_populates='users')

    @property
    def identity(self):
        return self.id

    @property
    def password(self):
        return self.hashed_password

    @property
    def rolenames(self):
        return []

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, user_id):
        return cls.query.get(user_id)

    def is_valid(self):
        return self.is_active


event_user = db.Table(
    'event_user',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), default='Untitled Event', nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    transactions = db.relationship('Transaction', back_populates='event')
    users = db.relationship('User', secondary=event_user, back_populates='events')


# class EventUser(db.Model):
#     __tablename__ = 'event_user'
#     event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
#     username = db.Column(db.String(80), db.ForeignKey('user.username'), primary_key=True)


transaction_user = db.Table(
    'transaction_user',
    db.Column('transaction_id', db.Integer, db.ForeignKey('transaction.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('amount', db.Float, nullable=False)
)


class Transaction(db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), default='Untitled', nullable=False)
    category = db.Column(db.String(80), default='General', nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    event = db.relationship('Event', back_populates='transactions')
    users = db.relationship('User', secondary=transaction_user, back_populates='transactions')


# class TransactionUser(db.Model):
#     __tablename__ = 'transaction_user'
#     transaction_id = db.Column(db.Integer, db.ForeignKey('event_transaction.id'), primary_key=True)
#     username = db.Column(db.String(80), db.ForeignKey('user.username'), primary_key=True)
#     amount = db.Column(db.Float, nullable=False)


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
