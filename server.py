from secrets import token_urlsafe
from flask import Flask, render_template, request, make_response, redirect, url_for
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import json
import httplib2
import random
import string
import requests
from database_schema import Base, User, UserSession, Category, Item
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
import smtplib
import datetime

app = Flask(__name__)

engine = create_engine(
    'sqlite:///database.db',
    connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def session_lookup(request, db_session):
    def manage_session(f):
        def inner(*args, **kwargs):
            session = {'logged_in': None, 'flash': [], 'flash_next': []}
            record = None
            now = datetime.datetime.now()
            if 'session_id' in request.cookies:
                # todo: sanitize input
                record = db_session.query(UserSession).filter_by(id=request.cookies['session_id']).one()
                if record.login_exp_time is not None and record.login_exp_time > now:
                    session['logged_in'] = record.user_email
                session['flash'] = record.flash.split(',')
            new_session = session.copy()
            response = make_response(f(*args, **kwargs, user_session=new_session))
            if record is None or session['logged_in'] != new_session['logged_in']:
                record = UserSession(
                    id=token_urlsafe(32),
                    user_email=new_session['logged_in'],
                    init_time=now,
                    login_exp_time=None)
                db_session.add(record)
                response.set_cookie('session_id', record.id)
            record.login_exp_time = now + datetime.timedelta(minutes=2)
            record.flash = ''  # todo
            db_session.commit()
            return response

        return inner

    return manage_session


@app.route("/", endpoint='home')
@app.route("/home", endpoint='home')
@session_lookup(request, session)
def home(user_session):
    categories = session.query(Category).all()
    return render_template("home.html", categories=categories, loggedin=user_session['logged_in'] is not None)


@app.route('/logout', endpoint='logout')
@session_lookup(request, session)
def logout(user_session):
    user_session['logged_in'] = None
    # todo: flash
    return redirect(url_for('home'))


@app.route("/login", endpoint='login', methods=['GET', 'POST'])
@session_lookup(request, session)
def login(user_session):
    if user_session['logged_in'] is not None:
        # todo: flash
        return redirect(url_for('home'))

    if request.method == 'GET':
        return render_template("login.html")

    user = session.query(User).filter_by(email=request.form['email']).one()

    if user.password == request.form['password']:
        user_session['logged_in'] = user.email
        # todo: flash login notification
        return redirect(url_for('home'))

    # todo: flash login failed notification
    return redirect(url_for('login'))


@app.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'GET':
        return render_template("sign_up.html")

    # todo: if existing email return error

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


@app.route("/check-email")
def check_email_message():
    return 'Check your email'


@app.route("/set-password", methods=['GET', 'POST'])
def set_password():
    token = (request.args if request.method == 'GET' else request.form)['token']
    user = session.query(User).filter_by(email_verification_token=token).one()

    if request.method == 'GET':
        if user.password is None:
            return render_template("initial_password_set.html", token=token)
        else:
            return render_template("password_reset.html", token=token)
    else:
        # todo: flash helpful message
        user.password = request.form['password']
        session.commit()
        return redirect(url_for('login'))


@app.route('/category/<name>/')
def category(name):
    c = session.query(Category).filter_by(name=name).one()
    items = session.query(Item).filter_by(category=name).all()
    return render_template('category_page.html', name=c.name, items=items)


@app.route('/item/<category>/<item>')
def item(category, item):
    item = session.query(Item).filter_by(category=category, item=item).one()
    return render_template('item_page.html', item=item)


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
