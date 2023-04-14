from flask import jsonify, request
import flask_praetorian

from app import app
from models import *


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
            'date': datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
            'owner': user.username,
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

        all_payments = data.get('payments')
        for t in all_payments:
            new_payment_data = {
                'name': t.get('place'),
                'reason': t.get('reason'),
                'event_id': new_event.id
            }
            new_payment = payment(**new_payment_data)
            db.session.add(new_payment)
            db.session.commit()

            all_cost = t.get('expenses')
            all_paid = t.get('paid')
            for i, user in enumerate(new_event_users):
                new_payment_user_data = {
                    'payment_id': new_payment.id,
                    'user_id': user.id,
                    'cost': all_cost[i],
                    'paid': all_paid[i]
                }
                new_payment_user = payment_user.insert().values(**new_payment_user_data)
                db.session.execute(new_payment_user)
                user.payments.append(new_payment)
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
