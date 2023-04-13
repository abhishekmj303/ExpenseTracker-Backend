from flask import jsonify, request
import flask_praetorian

from app import app, db, guard


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
