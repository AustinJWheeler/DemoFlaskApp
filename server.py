from secrets import token_urlsafe
from flask import Flask, render_template, request, make_response, redirect, url_for
from database_schema import Base, User, UserSession, Category, Item
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import smtplib
import datetime
from session_manager import session_lookup

import json
from flask import jsonify
from authlib.flask.client import OAuth
import bcrypt

app = Flask(__name__)

engine = create_engine(
    'sqlite:///database.db',
    connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)
app.config['GOOGLE_ID'] = "744904024585-9m8auns9dcl6pgfvdkneno66cvm58fik.apps.googleusercontent.com"
app.config['GOOGLE_SECRET'] = "X0zZmWtSrhlq6TAMCl_w0l-D"
app.debug = True
app.secret_key = 'development'
oauth = OAuth(app)

google = oauth.register(
    'google',
    client_id=app.config.get('GOOGLE_ID'),
    client_secret=app.config.get('GOOGLE_SECRET'),
    client_kwargs={
        'scope': 'openid profile email'
    },
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)


@app.route('/google-login')
def google_login():
    return oauth.google.authorize_redirect(url_for('authorized', _external=True))


@app.route('/callback', endpoint='authorized')
@session_lookup(request, session)
def authorized(user_session):
    resp = oauth.google.authorize_access_token()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    email = json.loads(oauth.google.get('userinfo').text)['email']
    # todo: new email?
    user_session['logged_in'] = email
    user_session['flash'].append(('success', 'you are logged in via google'))
    return redirect(url_for('home'))


@app.route("/", endpoint='home')
@app.route("/home", endpoint='home')
@session_lookup(request, session)
def home(user_session):
    categories = session.query(Category).all()
    return render_template("home.html", categories=categories, **user_session['kwargs'])


@app.route('/settings', endpoint='user_settings', methods=['GET', 'POST'])
@session_lookup(request, session)
def user_settings(user_session):
    return render_template('user_settings.html', **user_session['kwargs'])


@app.route('/logout', endpoint='logout')
@session_lookup(request, session)
def logout(user_session):
    user_session['logged_in'] = None
    user_session['flash'].append(('success', 'you\'ve successfully logged out'))
    return redirect(url_for('home'))


@app.route("/login", endpoint='login', methods=['GET', 'POST'])
@session_lookup(request, session)
def login(user_session):
    if user_session['logged_in'] is not None:
        user_session['flash'].append(('success', 'You\'re already logged in'))
        return redirect(url_for('home'))

    if request.method == 'GET':
        return render_template("login.html", **user_session['kwargs'])

    user = session.query(User).filter_by(email=request.form['email']).all()
    if len(user) == 0:
        user_session['flash'].append(('danger', 'The email you have entered is incorrect'))
        return redirect(url_for('login'))
    user = user[0]

    if bcrypt.checkpw(request.form['password'].encode('utf-8'), user.password):
        user_session['logged_in'] = user.email
        return redirect(url_for('home'))

    user_session['flash'].append(('danger', 'The password you have entered is incorrect'))
    return redirect(url_for('login'))


@app.route("/sign-up", endpoint='sign_up', methods=['GET', 'POST'])
@session_lookup(request, session)
def sign_up(user_session):
    if user_session['logged_in'] is not None:
        user_session['flash'].append(('info', 'Please logout before creating a new account'))

    if request.method == 'GET':
        return render_template("sign_up.html", **user_session['kwargs'])

    # todo: if existing email return error

    if len(session.query(User).filter_by(email=request.form['email']).all()) != 0:
        user_session['flash'].append(
            ('danger', 'You already have an account. Click login to login to your existing account'))
        return redirect(url_for('sign_up'))

    token = token_urlsafe(32)
    email = request.form['email']

    newUser = User(
        email=email,
        email_verification_token=token)

    send_verification_email(
        email, url_for('set_password', _external=True) + '?token=' + token)

    # todo: keep me logged in

    session.add(newUser)
    session.commit()

    return redirect(url_for('check_email_message'))


@app.route('/add/<category>', endpoint='add', methods=['GET', 'POST'])
@session_lookup(request, session)
def add(category, user_session):
    if user_session['logged_in'] is None:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('add_item.html', **user_session['kwargs'])
    if len(session.query(Item).filter_by(category=category, item=request.form['item']).all()) != 0:
        user_session['flash'].append(
            ('danger', 'An item with this name already exists'))
        return redirect(url_for('category', category=category))

    newItem = Item(
        category=category,
        item=request.form['item'],
        description=request.form['description'],
        user_email=user_session['logged_in'])
    session.add(newItem)
    session.commit()

    return redirect(url_for('item', category=category, item=request.form['item']))


@app.route('/forgot-password', endpoint='forgot_password', methods=['GET', 'POST'])
@session_lookup(request, session)
def forgot_password(user_session):
    return 'Forgot Password'


@app.route("/check-email")
def check_email_message():
    return 'Check your email'


@app.route("/set-password", endpoint='set_password', methods=['GET', 'POST'])
@session_lookup(request, session)
def set_password(user_session):
    token = (request.args if request.method == 'GET' else request.form)['token']
    user = session.query(User).filter_by(email_verification_token=token).one()

    if request.method == 'GET':
        if user.password is None:
            return render_template("initial_password_set.html", token=token)
        return render_template("password_reset.html", token=token)

    user.password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
    session.commit()
    user_session['flash'].append(('success', 'Your password has been set'))
    return redirect(url_for('login'))


@app.route('/category/<name>/')
def category(name):
    c = session.query(Category).filter_by(name=name).one()
    items = session.query(Item).filter_by(category=name).all()
    return render_template('category_page.html', name=c.name, category=name, items=items)


@app.route('/item/<category>/<item>', endpoint='item')
@session_lookup(request, session)
def item(category, item, user_session):
    item = session.query(Item).filter_by(category=category, item=item).one()
    return render_template('item_page.html', category=category, item=item,
                           canedit=item.user_email == user_session['logged_in'])


@app.route('/edit/<category>/<item>', endpoint='edit', methods=['GET', 'POST'])
@session_lookup(request, session)
def edit(category, item, user_session):
    item = session.query(Item).filter_by(category=category, item=item).one()
    if item.user_email != user_session['logged_in']:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('edit_page.html', category=category, item=item,
                               canedit=item.user_email == user_session['logged_in'])
    item.item = request.form['item']
    item.description = request.form['description']
    session.commit()
    return redirect(url_for('item', item=item.item, category=category))


@app.route('/delete/<category>/<item>', endpoint='delete', methods=['GET', 'POST'])
@session_lookup(request, session)
def delete(category, item, user_session):
    item = session.query(Item).filter_by(category=category, item=item).one()
    if item.user_email != user_session['logged_in']:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('delete_page.html', category=category, item=item,
                               canedit=item.user_email == user_session['logged_in'])
    session.delete(item)
    session.commit()
    user_session['flash'].append(('success', item.item + ' has been deleted'))
    return redirect(url_for('category', name=category))


def send_verification_email(email, url):
    fromaddr = "austinwheelerj@gmail.com"
    email_password = "uafbypeosywnrsxb"
    text = """From: Web Server <from@fromdomain.com>
To: <{}>
MIME-Version: 1.0
Content-type: text/html
Subject: Verify your email

<h1>H1 here</h1>

<a href="{}">click here</a>
""".format(email, url)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, email_password)
    server.sendmail(fromaddr, email, text)
    server.quit()


@app.route("/all-categories")
def all_catagories():
    categories = session.query(Category).all()
    return render_template('all_catagories.html', categories=categories)


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
