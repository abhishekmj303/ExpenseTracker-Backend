import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_cors import CORS
from models import *

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.getcwd(), 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)


@app.route('/')
def home():
    return "Hello!!"


@app.route('/expense/<int:expense_id>', methods=['GET', 'POST', 'DELETE'])
def expense_api(expense_id):
    if request.method == 'GET':
        expense = Expense.query.filter_by(id=expense_id).first()
        return jsonify(expense), 200
    elif request.method == 'POST':
        data = request.get_json()
        expense = Expense(**data)
        db.session.add(expense)
        db.session.commit()
        resp = {'id': expense.id, 'message': 'Expense added', 'status': 'success'}
        return jsonify(resp), 201
    elif request.method == 'DELETE':
        expense = Expense.query.filter_by(id=expense_id).first()
        db.session.delete(expense)
        db.session.commit()
        resp = {'id': expense_id, 'message': 'Expense deleted', 'status': 'success'}
        return jsonify(resp), 200
