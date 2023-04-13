import os
from dotenv import load_dotenv
from flask import Flask
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
