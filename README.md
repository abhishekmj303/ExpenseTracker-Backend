# Expense Tracker Backend

## Setup

### Python virtual environment

```bash
pip install virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Database

```bash
flask db init
```

### Run

```bash
flask run
```

### Update Database

After change in models.py
```bash
flask db migrate
flask db upgrade
```