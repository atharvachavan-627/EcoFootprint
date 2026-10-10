"""ECOFOOTPRINT - educational local Flask app. NOT production-grade authentication."""
import json, os, re, secrets
from functools import wraps
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from services.calculator import ValidationError, calculate

BASE = os.path.dirname(os.path.abspath(__file__))
UF, KF = os.path.join(BASE, 'data', 'users.json'), os.path.join(BASE, 'data', '.secret_key')
app = Flask(__name__)
if not os.environ.get('SECRET_KEY') and not os.path.exists(KF):
    open(KF, 'w').write(secrets.token_hex(32))
app.secret_key = os.environ.get('SECRET_KEY') or open(KF).read()
PAGES = {'dashboard': 'Dashboard', 'calculator': 'Calculator', 'results': 'Results', 'simulator': 'Reduction Simulator',
         'report': 'My Report', 'history': 'History', 'learn': 'Learn & Act', 'profile': 'Profile'}

def users():
    try:
        return json.load(open(UF))
    except (OSError, ValueError):
        return {}

def public(u):
    return {k: u[k] for k in ('name', 'email', 'age', 'city')}

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if session.get('email') not in users():
            session.clear()
            if request.path.startswith('/api/'):
                return jsonify(error='Session expired. Please log in again.'), 401
            return redirect(url_for('login', msg='expired'))
        return f(*a, **k)
    return w

def check_profile(d, pw=True):
    name, email, city = [(d.get(k) or '').strip() for k in ('name', 'email', 'city')]
    if not name or not city or not email:
        return 'Please fill in all required fields.'
    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return 'Enter a valid email address.'
    try:
        if not 10 <= int(d.get('age')) <= 100:
            raise ValueError
    except (TypeError, ValueError):
        return 'Age must be a number between 10 and 100.'
    if pw:
        if len(d.get('password') or '') < 8:
            return 'Password must be at least 8 characters.'
        if d.get('password') != d.get('confirm'):
            return 'Passwords do not match.'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('auth.html', mode='login')

@app.route('/register')
def register():
    return render_template('auth.html', mode='register')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login', msg='bye'))

@app.post('/api/register')
def api_register():
    d = request.get_json(silent=True) or {}
    err = check_profile(d)
    u = users()
    email = (d.get('email') or '').strip().lower()
    if not err and email in u:
        err = 'An account with this email already exists.'
    if err:
        return jsonify(error=err), 400
    u[email] = dict(name=d['name'].strip(), email=email, age=int(d['age']), city=d['city'].strip(), pw=generate_password_hash(d['password']))
    json.dump(u, open(UF, 'w'), indent=1)
    return jsonify(ok=True)

@app.post('/api/login')
def api_login():
    d = request.get_json(silent=True) or {}
    u = users().get((d.get('email') or '').strip().lower())
    if not u or not check_password_hash(u['pw'], d.get('password') or ''):
        return jsonify(error='Incorrect email or password.'), 401
    session.clear()
    session['email'] = u['email']
    return jsonify(ok=True)

@app.post('/api/profile')
@login_required
def api_profile():
    d = request.get_json(silent=True) or {}
    d['email'] = session['email']
    err = check_profile(d, pw=False)
    if err:
        return jsonify(error=err), 400
    u = users()
    u[session['email']].update(name=d['name'].strip(), age=int(d['age']), city=d['city'].strip())
    json.dump(u, open(UF, 'w'), indent=1)
    return jsonify(ok=True)

@app.post('/api/calculate')
@login_required
def api_calculate():
    try:
        return jsonify(calculate(request.get_json(silent=True)))
    except ValidationError as e:
        return jsonify(error=str(e)), 400
    except Exception:
        return jsonify(error='Calculation failed. Please check your inputs.'), 500

def make_page(p):
    @login_required
    def view():
        return render_template('app.html', page=p, title=PAGES[p], pages=PAGES, user=public(users()[session['email']]))
    return view

for _p in PAGES:
    app.add_url_rule('/' + _p, _p, make_page(_p))

if __name__ == '__main__':
    app.run()
