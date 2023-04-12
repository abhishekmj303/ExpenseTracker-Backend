import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_migrate import Migrate
import flask_praetorian
from flask_mail import Mail, Message
from flask_cors import CORS
from models import *

load_dotenv()

app = Flask(__name__)

# Enable CORS
CORS(app)

# Setup database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.getcwd(), 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

# Setup user-authentication (https://flask-praetorian.readthedocs.io/en/latest/flask_praetorian.html)
app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
app.config["JWT_ACCESS_LIFESPAN"] = {"hours": 24}
app.config["JWT_REFRESH_LIFESPAN"] = {"days": 30}
app.config["PRAETORIAN_ROLES_DISABLED"] = True
app.config["PRAETORIAN_CONFIRMATION_SENDER"] = os.getenv('EMAIL')
guard = flask_praetorian.Praetorian()
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


@app.route('/login', methods=['POST'])
def login_api():
    req = request.get_json(force=True)
    username = req.get("username", None)
    password = req.get("password", None)
    user = guard.authenticate(username, password)
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401
    if not user.is_confirm:
        return jsonify({"message": "Please confirm your account"}), 401
    resp = {"access_token": guard.encode_jwt_token(user), "message": "Login successful"}
    return jsonify(resp), 200


@app.route('/signup', methods=['POST'])
def signup_api():
    req = request.get_json(force=True)
    req['hashed_password'] = guard.hash_password(req.get('password', None))
    del req['password']
    new_username = req.get('username', None)
    if User.query.filter_by(username=new_username).first():
        resp = {'message': f'username {new_username} already exists'}
        return jsonify(resp), 409
    new_user = User(**req)
    db.session.add(new_user)
    db.session.commit()
    guard.send_registration_email(
        new_user.email, new_user,
        subject="Confirm your account",
        confirmation_uri="http://localhost:5000/verify"
    )
    resp = {'message': f'successfully sent registration email to user {new_user.email}'}
    return jsonify(resp), 200


@app.route('/verify', methods=['GET'])
def verify_api():
    token = request.args.get('token', None)
    if not token:
        return jsonify({"message": "Missing token"}), 400
    try:
        user = guard.get_user_from_registration_token(token)
        if user.is_confirm:
            return jsonify({"message": "User already confirmed"}), 400
        User.query.filter_by(id=user.id).update({'is_confirm': True})
        db.session.commit()
        resp = {'message': f'user {user.username} successfully confirmed'}
        return jsonify(resp), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 400


# def refresh_jwt(token):
#     try:
#         user = guard.get_user_from_refresh_token(token)
#         return guard.encode_jwt_token(user)
#     except Exception as e:
#         return jsonify({"message": str(e)}), 400


@app.route('/mail')
def home():
    msg = Message('Hello', sender=os.getenv('EMAIL'), recipients=['siddeshdslr@gmail.com', 'abhishekmj303@gmail.com'])
    msg.body = "This is a test email sent using Flask-Mail."
    mail.send(msg)
    return "Sent"


@app.route('/expense', methods=['GET', 'POST', 'DELETE'])
@flask_praetorian.auth_required
def expense_api():
    user = flask_praetorian.current_user()
    if request.method == 'GET':
        expenses = Expense.query.filter(
            (Expense.username == user.username) |
            ((Expense.other_username == user.username) & (Expense.is_private == False))
        ).all()
        return jsonify(expenses), 200
    elif request.method == 'POST':
        data = request.get_json()
        expense = Expense(**data)
        db.session.add(expense)
        db.session.commit()
        resp = {'id': expense.id, 'message': 'Expense added', 'status': 'success'}
        return jsonify(resp), 201
    elif request.method == 'DELETE':
        expense = Expense.query.filter().first()
        db.session.delete(expense)
        db.session.commit()
        resp = {'message': 'Expense deleted', 'status': 'success'}
        return jsonify(resp), 200


@app.route('/event', methods=['GET', 'POST', 'DELETE'])
@flask_praetorian.auth_required
def event_api():
    if request.method == 'GET':
        user = flask_praetorian.current_user()
        events = Event.query.filter().all()
        return jsonify(events), 200
