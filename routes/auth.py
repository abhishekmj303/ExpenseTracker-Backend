from flask import jsonify, request
import flask_praetorian

from app import app
from models import *

guard = flask_praetorian.Praetorian()


@app.route('/login', methods=['POST'])
def login_api():
    req = request.get_json(force=True)
    username = req.get("username", None)
    password = req.get("password", None)
    email = req.get("email", None)
    if not username:
        username = User.query.filter_by(email=email).first().username
    user = guard.authenticate(username, password)
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401
    if not user.is_confirm:
        return jsonify({"message": "Please confirm your account"}), 401
    access_token = guard.encode_jwt_token(user)
    resp = jsonify({
        "message": "Login successful",
        "status": "success"
    })
    resp.headers.add('Set-Cookie', f'access_token={access_token}; Domain=expensetracker-backend-production.up.railway.app; HttpOnly;')
    return resp, 200


@app.route('/register', methods=['POST'])
def signup_api():
    req = request.get_json(force=True)
    new_user_data = {
        'username': req.get('username'),
        'email': req.get('email'),
        'hashed_password': guard.hash_password(req.get('password')),
        'name': req.get('name'),
        'upi': req.get('upi'),
        'date_joined': datetime.now(),
    }
    new_user = User(**new_user_data)
    old_user = User.query.filter_by(username=new_user_data['username']).first()
    if old_user:
        if old_user.is_confirm:
            resp = {'message': f'username {new_user_data["username"]} already exists', 'status': 'fail'}
            return jsonify(resp), 409
        else:
            db.session.delete(old_user)
            db.session.commit()
    db.session.add(new_user)
    db.session.commit()
    guard.send_registration_email(
        new_user.email, new_user,
        subject="Confirm your account",
        confirmation_uri="https://expensetracker-backend-production.up.railway.app/verify"
    )
    resp = {'message': f'successfully sent registration email to user {new_user.email}'}
    return jsonify(resp), 200


@app.route('/verify', methods=['GET'])
def verify_api():
    token = request.args.get('token')
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


@app.route('/logout', methods=['POST'])
def logout_api():
    resp = jsonify({"message": "Successfully logged out"})
    resp.headers.add('Set-Cookie', 'access_token=; HttpOnly;')
    return resp, 200
