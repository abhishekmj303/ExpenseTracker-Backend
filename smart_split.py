from models import *
from sqlalchemy import text


def split_expenses(event: Event):
    # SQLQUERY = text("""SELECT * FROM PAYMENT_USER WHERE PAYMENT_ID IN (SELECT PAYMENT_ID FROM PAYMENTS WHERE EVENT_ID = %s)""")
    payments = db.session.query(Payment, payment_user).join(payment_user).filter(Payment.event_id == event.id).all()
    # payments = db.session.execute(SQLQUERY % event.id)
    user_final = {}
    for payment in payments:
        user_final[payment.user_id] = user_final.get(payment.user_id, 0) - payment.cost + payment.paid
    user_final_sorted = sorted(user_final.items(), key=lambda x: x[1])
    pair_expenses = []
    while len(user_final_sorted) > 1:
        if user_final_sorted[0][1] == 0:
            user_final_sorted.pop(0)
        elif user_final_sorted[-1][1] == 0:
            user_final_sorted.pop(-1)
        else:
            pair_expenses.append((user_final_sorted[0][0], user_final_sorted[-1][0], user_final_sorted[0][1]))
            user_final_sorted[0] = (user_final_sorted[0][0], user_final_sorted[0][1] + user_final_sorted[-1][1])
            user_final_sorted.pop(-1)
    return pair_expenses


def add_expenses(event: Event):
    expenses = split_expenses(event)
    for expense in expenses:
        new_expense_data = {
            'username': User.query.filter_by(id=expense[0]).first().username,
            'event_id': event.id,
            'amount': expense[2],
            'reason': event.name,
            'date': event.date,
            'other_username': User.query.filter_by(id=expense[1]).first().username,
        }
        new_expense = Expense(**new_expense_data)
        db.session.add(new_expense)
        db.session.commit()