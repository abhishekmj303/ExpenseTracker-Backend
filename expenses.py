from flask import jsonify, request
import flask_praetorian
from sqlalchemy import func

from app import app
from models import *


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
