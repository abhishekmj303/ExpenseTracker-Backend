from flask import request, jsonify
import flask_praetorian
from datetime import date

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

@app.route('/stats/users', methods=['GET'])
@flask_praetorian.auth_required
def user_stats_api():
    user = flask_praetorian.current_user()
    user_expense = user_expenses_query(user).all()
    group_users = {}
    for expense in user_expense:
        group_users[expense.user] = group_users.get(expense.user, 0) + expense.amount
    all_users = list(group_users.keys())
    all_amounts = list(group_users.values())
    resp = {'incoming': [], 'outgoing': []}
    for i in range(len(all_users)):
        if all_amounts[i] > 0:
            resp['incoming'].append({'name': all_users[i], 'value': all_amounts[i]})
        else:
            resp['outgoing'].append({'name': all_users[i], 'value': -all_amounts[i]})
    return jsonify(resp), 200


@app.route('/stats/date', methods=['POST'])
@flask_praetorian.auth_required
def date_stats_api():
    user = flask_praetorian.current_user()
    data = request.get_json()
    date1, date2 = data['date1'][:10].split('-'), data['date2'][:10].split('-')
    print(date1, date2)
    date1, date2 = date(*map(int, date1)), date(*map(int, date2))
    expenses = user_expenses_query(user).filter(
        (Expense.date >= date1) & (Expense.date <= date2)
    ).all()
    number_of_days = int((date2 - date1).days)
    resp = [{'name': f'Day{i+1}', 'pay': 0, 'receive': 0} for i in range(number_of_days)]
    for expense in expenses:
        day = int((expense.date.date() - date1).days)
        if expense.amount > 0:
            resp[day]['receive'] += expense.amount
        else:
            resp[day]['pay'] += expense.amount
    return jsonify(resp), 200
