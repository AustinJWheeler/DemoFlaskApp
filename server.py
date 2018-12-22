import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database_schema import Base, User, Category, Item
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from session_manager import session_lookup
import json
from authlib.flask.client import OAuth

app = Flask(__name__)

engine = create_engine(
    'sqlite:///database.db',
    connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

client_secrets = json.loads(open('client_secrets.json', 'r').read())['web']

app.secret_key = 'development'
oauth = OAuth(app)

google = oauth.register(
    'google',
    client_id=client_secrets['client_id'],
    client_secret=client_secrets['client_secret'],
    client_kwargs={
        'scope': 'openid profile email'
    },
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url=client_secrets['token_uri'],
    authorize_url=client_secrets['auth_uri'],
)


@app.route("/", endpoint='home')
@app.route("/home", endpoint='home')
@session_lookup(request, session)
def home(user_session):
    categories = session.query(Category).all()
    items = session.query(Item).all()[:-11:-1]
    return render_template("home.html", categories=categories, items=items,
                           **user_session['kwargs'])


@app.route("/all-categories", endpoint='all_categories')
@session_lookup(request, session)
def all_categories(user_session):
    categories = session.query(Category).all()
    return render_template('all_categories.html', categories=categories,
                           **user_session['kwargs'])


@app.route("/all-categories.json", endpoint='all_categories_json')
@session_lookup(request, session)
def all_categories_json(user_session):
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/catalog/<name>/', endpoint='category')
@session_lookup(request, session)
def category(name, user_session):
    c = session.query(Category).filter_by(name=name).one()
    items = session.query(Item).filter_by(category=name).all()
    return render_template('category_page.html', name=c.name, category=name,
                           items=items, **user_session['kwargs'])


@app.route('/catalog/<category>/<item>', endpoint='item')
@session_lookup(request, session)
def item(category, item, user_session):
    item = session.query(Item).filter_by(category=category, item=item).one()
    return render_template('item_page.html', category=category, item=item,
                           canedit=item.user_email == user_session[
                               'logged_in'], **user_session['kwargs'])


@app.route('/add', endpoint='add', methods=['GET', 'POST'])
@session_lookup(request, session)
def add(user_session):
    if user_session['logged_in'] is None:
        return redirect(url_for('login'))
    if request.method == 'GET':
        categories = session.query(Category).all()
        return render_template('add_item.html', categories=categories,
                               **user_session['kwargs'])
    if len(session.query(Item).filter_by(
            category=request.form['category'],
            item=request.form['item']).all()) != 0:
        user_session['flash'].append(
            ('danger', 'An item with this name already exists'))
        return redirect(url_for('all_categories'))

    newItem = Item(
        category=request.form['category'],
        item=request.form['item'],
        description=request.form['description'],
        user_email=user_session['logged_in'])
    session.add(newItem)
    session.commit()

    return redirect(url_for('item', category=request.form['category'],
                            item=request.form['item']))


@app.route('/edit/<category>/<item>', endpoint='edit', methods=['GET', 'POST'])
@session_lookup(request, session)
def edit(category, item, user_session):
    item = session.query(Item).filter_by(category=category, item=item).one()
    if item.user_email != user_session['logged_in']:
        return redirect(url_for('login'))
    if request.method == 'GET':
        categories = session.query(Category).all()
        return render_template('edit_page.html', category=category, item=item,
                               categories=categories,
                               canedit=item.user_email == user_session[
                                   'logged_in'], **user_session['kwargs'])
    item.item = request.form['item']
    item.description = request.form['description']
    item.category = request.form['category']
    session.commit()
    return redirect(url_for('item', item=item.item, category=item.category))


@app.route('/delete/<category>/<item>', endpoint='delete',
           methods=['GET', 'POST'])
@session_lookup(request, session)
def delete(category, item, user_session):
    item = session.query(Item).filter_by(category=category, item=item).one()
    if item.user_email != user_session['logged_in']:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template('delete_page.html', category=category,
                               item=item,
                               canedit=item.user_email == user_session[
                                   'logged_in'], **user_session['kwargs'])
    session.delete(item)
    session.commit()
    user_session['flash'].append(('success', item.item + ' has been deleted'))
    return redirect(url_for('category', name=category))


@app.route('/logout', endpoint='logout')
@session_lookup(request, session)
def logout(user_session):
    user_session['logged_in'] = None
    user_session['flash'].append(
        ('success', 'you\'ve successfully logged out'))
    return redirect(url_for('home'))


@app.route("/login", endpoint='login')
@session_lookup(request, session)
def login(user_session):
    if user_session['logged_in'] is not None:
        user_session['flash'].append(('success', 'You\'re already logged in'))
        return redirect(url_for('home'))

    return render_template("login.html", **user_session['kwargs'])


@app.route('/google-login')
def google_login():
    return oauth.google.authorize_redirect(
        url_for('authorized', _external=True))


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

    user = session.query(User).filter_by(email=email).all()
    if len(user) == 0:
        user = User(email=email)
        session.add(user)
        session.commit()

    user_session['logged_in'] = email
    user_session['flash'].append(('success', 'you are logged in via google'))

    requests.post('https://accounts.google.com/o/oauth2/revoke',
                  params={'token': resp['access_token']},
                  headers={
                      'content-type': 'application/x-www-form-urlencoded'})

    return redirect(url_for('home'))


if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
