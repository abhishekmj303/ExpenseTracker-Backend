import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from sqlalchemy import func
from flask_migrate import Migrate
from flask_mail import Mail, Message
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)

# Enable CORS
CORS(app)

# Setup database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.getcwd(), 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
from models import *
db.init_app(app)
migrate = Migrate(app, db, render_as_batch=True)

# Setup user-authentication (https://flask-praetorian.readthedocs.io/en/latest/flask_praetorian.html)
app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
app.config["JWT_ACCESS_LIFESPAN"] = {"hours": 24}
app.config["JWT_REFRESH_LIFESPAN"] = {"days": 30}
app.config["PRAETORIAN_ROLES_DISABLED"] = True
app.config["PRAETORIAN_CONFIRMATION_SENDER"] = os.getenv('EMAIL')
from auth import *
with app.app_context():
    guard.init_app(app, User)


# Setup mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('EMAIL')
app.config['MAIL_PASSWORD'] = os.getenv('PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


@app.route('/mail')
def home():
    msg = Message('Hello', sender=os.getenv('EMAIL'), recipients=['siddeshdslr@gmail.com', 'abhishekmj303@gmail.com'])
    msg.body = "This is a test email sent using Flask-Mail."
    mail.send(msg)
    return "Sent"


@app.route('/users', methods=['GET', 'POST'])
@flask_praetorian.auth_required
def user_api():
    if request.method == 'GET':
        user = flask_praetorian.current_user()
        resp = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'name': user.name,
            'upi': user.upi,
            'date_joined': user.date_joined
        }
        return jsonify(resp), 200
    elif request.method == 'POST':
        data = request.get_json()
        user = flask_praetorian.current_user()
        if data.get('username'):
            user.username = data['username']
        if data.get('name'):
            user.name = data['name']
        if data.get('upi'):
            user.upi = data['upi']
        if data.get('email') != user.email:
            user.email = data['email']
            user.is_confirm = False
            guard.send_registration_email(
                user.email, user,
                subject="Confirm new email",
                confirmation_uri="http://localhost:5000/verify"
            )
        db.session.commit()
        resp = {'message': 'User updated', 'status': 'success'}
        return jsonify(resp), 201


@app.route('/users/password', methods=['POST'])
@flask_praetorian.auth_required
def password_api():
    data = request.get_json()
    user = flask_praetorian.current_user()
    if guard.authenticate(user.username, data['old_password']):
        user.hashed_password = guard.hash_password(data['new_password'])
        db.session.commit()
        access_token = guard.encode_jwt_token(user)
        resp = jsonify({'message': 'Password updated', 'status': 'success'})
        resp.headers.add('Set-Cookie', f'access_token={access_token}; HttpOnly;')
        return jsonify(resp), 201
    else:
        resp = {'message': 'Incorrect password', 'status': 'error'}
        return jsonify(resp), 401


@app.route('/expenses/total', methods=['GET'])
@flask_praetorian.auth_required
def total_expense_api():
    user = flask_praetorian.current_user()
    this_incoming = db.session.query(func.sum(Expense.amount)).filter(
        ((Expense.username == user.username) & (Expense.amount > 0))
    ).scalar()
    other_incoming = db.session.query(func.sum(Expense.amount)).filter(
        ((Expense.other_username == user.username) & (Expense.is_private == False) & (Expense.amount < 0))
    ).scalar()
    this_outgoing = db.session.query(func.sum(Expense.amount)).filter(
        ((Expense.username == user.username) & (Expense.amount < 0))
    ).scalar()
    other_outgoing = db.session.query(func.sum(Expense.amount)).filter(
        ((Expense.other_username == user.username) & (Expense.is_private == False) & (Expense.amount > 0))
    ).scalar()
    incoming = float(this_incoming or 0) - float(other_incoming or 0)
    outgoing = float(this_outgoing or 0) - float(other_outgoing or 0)
    total_balance = float(incoming or 0) + float(outgoing or 0)
    resp = {
        'username': user.username,
        'total_balance': total_balance,
        'total_incoming': incoming,
        'total_outgoing': outgoing
    }
    return jsonify(resp), 200


@app.route('/expenses/users', methods=['GET'])
@flask_praetorian.auth_required
def user_expense_api():
    user = flask_praetorian.current_user()
    this_total = db.session.query(
        Expense.other_username.label('user'),
        func.sum(Expense.amount).label('amount_sum')
    ).filter(
        (Expense.username == user.username)
    ).group_by(Expense.other_username)
    other_total = db.session.query(
        Expense.username.label('user'),
        func.sum(-Expense.amount).label('amount_sum')
    ).filter(
        (Expense.other_username == user.username) & (Expense.is_private == False)
    ).group_by(Expense.username)
    total = this_total.union(other_total).all()
    user_expense = {}
    for expense in total:
        if expense.user not in user_expense:
            user_expense[expense.user] = expense.amount_sum
        else:
            user_expense[expense.user] += expense.amount_sum
    return jsonify(user_expense), 200


@app.route('/expenses', methods=['GET', 'POST'])
@flask_praetorian.auth_required
def expense_api():
    user = flask_praetorian.current_user()
    if request.method == 'GET':
        this_expenses = Expense.query(
            Expense.other_username.label('user'),
            Expense.amount,
            Expense.category.label('reason'),
            Expense.date,
            Expense.is_private
        ).filter(
            (Expense.username == user.username)
        )
        other_expenses = Expense.query(
            Expense.username.label('user'),
            -Expense.amount,
            Expense.category.label('reason'),
            Expense.date,
            Expense.is_private
        ).filter(
            (Expense.other_username == user.username) & (Expense.is_private == False)
        )
        expenses = this_expenses.union(other_expenses).all()
        return jsonify(expenses), 200
    elif request.method == 'POST':
        data = request.get_json()
        new_expense_data = {
            'other_username': data.get('other_username'),
            'amount': data.get('amount'),
            'category': data.get('reason'),
            'date': data.get('date'),
            'is_private': data.get('is_private')
        }
        expense = Expense(**new_expense_data)
        db.session.add(expense)
        db.session.commit()
        resp = {'id': expense.id, 'message': 'Expense added', 'status': 'success'}
        return jsonify(resp), 201


@app.route('/expenses/<exp_id>', methods=['DELETE'])
@flask_praetorian.auth_required
def expense_delete_api(exp_id):
    expense = Expense.query.filter_by(id=exp_id).first()
    if not expense:
        resp = {'message': 'Expense not found', 'status': 'fail'}
        return jsonify(resp), 404
    db.session.delete(expense)
    db.session.commit()
    resp = {'id': expense.id, 'message': 'Expense deleted', 'status': 'success'}
    return jsonify(resp), 200


@app.route('/events', methods=['GET', 'POST'])
@flask_praetorian.auth_required
def event_api():
    user = flask_praetorian.current_user()
    if request.method == 'GET':
        events = user.events
        return jsonify(events), 200
    elif request.method == 'POST':
        data = request.get_json()
        new_event_data = {
            'name': data.get('event_name'),
            'date': datetime.fromisoformat(data.get('date'))
        }
        new_event = Event(**new_event_data)
        new_event_users = [
            User.query.filter(User.username == username).first()
            for username in data.get('users')
        ]
        db.session.add(new_event)
        for u in new_event_users:
            new_event.users.append(u)
        db.session.commit()
        resp = {'id': new_event.id, 'message': 'Event added'}
        return jsonify(resp), 201


@app.route('/events/<event_id>', methods=['DELETE'])
@flask_praetorian.auth_required
def event_delete_api(event_id):
    event = Event.query.filter_by(id=event_id).first()
    if event is None:
        resp = {'message': 'Event not found', 'status': 'fail'}
        return jsonify(resp), 404
    if event.owner != flask_praetorian.current_user().username:
        resp = {'message': 'You are not the owner of this event', 'status': 'fail'}
        return jsonify(resp), 403
    db.session.delete(event)
    db.session.commit()
    resp = {'id': event.id, 'message': 'Event deleted'}
    return jsonify(resp), 200
