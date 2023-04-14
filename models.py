from datetime import datetime
from dataclasses import dataclass
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
# from flask_praetorian import SQLAlchemyUserMixin

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(metadata=metadata)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(80))
    upi = db.Column(db.String(30))
    date_joined = db.Column(db.DateTime, nullable=False)
    is_confirm = db.Column(db.Boolean, default=False, server_default="false")
    is_active = db.Column(db.Boolean, default=True, server_default="true")

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


# event_user = db.Table(
#     'event_user',
#     db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
#     db.Column('user_name', db.Integer, db.ForeignKey('user.username'))
# )


@dataclass
class Event(db.Model):
    __tablename__ = 'event'
    id: int
    name: str
    date: datetime.date
    owner: str
    # payments: list
    # users: list

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), default='Untitled Event', nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    owner = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    # payments = db.relationship('Payment', back_populates='event')


class EventUser(db.Model):
    __tablename__ = 'event_user'
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), primary_key=True)


# payment_user = db.Table(
#     'payment_user',
#     db.Column('payment_id', db.Integer, db.ForeignKey('payment.id')),
#     db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
#     db.Column('cost', db.Float, default=0, nullable=False),
#     db.Column('paid', db.Float, default=0, nullable=False)
# )


@dataclass
class Payment(db.Model):
    __tablename__ = 'payment'
    id: int
    name: str
    reason: str
    event_id: int
    # users: list

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), default='Untitled', nullable=False)
    reason = db.Column(db.String(80), default='General')
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)


class PaymentUser(db.Model):
    __tablename__ = 'payment_user'
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), primary_key=True)
    cost = db.Column(db.Float, default=0, nullable=False)
    paid = db.Column(db.Float, default=0, nullable=False)


@dataclass
class Expense(db.Model):
    __tablename__ = 'expense'
    id: int
    username: str
    other_username: str
    amount: float
    event_id: int
    name: str
    reason: str
    date: datetime
    is_private: bool

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    other_username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
    name = db.Column(db.String(80))
    reason = db.Column(db.String(80), default='General')
    date = db.Column(db.DateTime, nullable=False)
    is_private = db.Column(db.Boolean, default=False, nullable=False)
    cleared = db.Column(db.Boolean, default=False, nullable=False)
