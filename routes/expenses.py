from flask import jsonify, request
import flask_praetorian
from sqlalchemy import func

from app import app
from models import *


def user_expenses_query(user: User):
    self_expenses = Expense.query.with_entities(
        Expense.other_username.label('user'),
        Expense.amount,
        Expense.reason,
        Expense.date,
        Expense.is_private
    ).filter(
        (Expense.username == user.username)
    )
    other_expenses = Expense.query.with_entities(
        Expense.username.label('user'),
        -Expense.amount,
        Expense.reason,
        Expense.date,
        Expense.is_private
    ).filter(
        (Expense.other_username == user.username) & (Expense.is_private == False)
    )
    expenses = self_expenses.union(other_expenses)
    return expenses


@app.route('/expenses/total', methods=['GET'])
@flask_praetorian.auth_required
def total_expense_api():
    user = flask_praetorian.current_user()
    expenses = user_expenses_query(user)
    incoming = 0
    outgoing = 0
    for expense in expenses:
        if expense.amount > 0:
            incoming += expense.amount
        else:
            outgoing += expense.amount
    total_balance = incoming + outgoing
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
    user_expense = user_expenses_query(user).all()
    group_users = {}
    for expense in user_expense:
        group_users[expense.user] = group_users.get(expense.user, 0) + expense.amount
    group_users = [{'user': k, 'amount': v} for k, v in group_users.items()]
    return jsonify(group_users), 200


@app.route('/expenses/past/<days>', methods=['GET'])
@flask_praetorian.auth_required
def past_expense_api(days):
    user = flask_praetorian.current_user()
    expenses = user_expenses_query(user).filter(
        Expense.date > func.dateadd('day', -int(days), func.now())
    ).all()
    expenses = [dict(e._asdict()) for e in expenses]
    return jsonify(expenses), 200


@app.route('/expenses', methods=['GET', 'POST'])
@flask_praetorian.auth_required
def expense_api():
    user = flask_praetorian.current_user()
    if request.method == 'GET':
        expenses = user_expenses_query(user).all()
        expenses = [dict(e._asdict()) for e in expenses]
        return jsonify(expenses), 200
    elif request.method == 'POST':
        data = request.get_json()
        new_expense_data = {
            'other_username': data.get('other_username'),
            'amount': data.get('amount'),
            'reason': data.get('reason'),
            'date': datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
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
