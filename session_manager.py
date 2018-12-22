from secrets import token_urlsafe
from flask import make_response, Response
from database_schema import UserSession
import datetime


def session_lookup(request, db_session):
    def manage_session(f):
        def inner(*args, **kwargs):
            session = {'logged_in': None, 'flash': [],
                       'kwargs': {'flash': [], 'loggedin': False}}
            record = None
            now = datetime.datetime.now()
            if 'session_id' in request.cookies:
                record = db_session.query(UserSession).filter_by(
                    id=request.cookies['session_id']).all()
                if len(record) == 0:
                    response = Response(response='Server Error',
                                        status='500 Internal Server Error')
                    response.set_cookie('session_id', '', expires=now)
                    return response
                record = record[0]
                if record.login_exp_time is not None and \
                        record.login_exp_time > now:
                    session['logged_in'] = record.user_email
                session['kwargs']['flash'] = to_tup_list(record.flash)
                session['kwargs']['loggedin'] = session[
                                                    'logged_in'] is not None
            new_session = session.copy()
            response = make_response(
                f(*args, **kwargs, user_session=new_session))
            if record is None or \
                    session['logged_in'] != new_session['logged_in']:
                record = UserSession(
                    id=token_urlsafe(32),
                    user_email=new_session['logged_in'],
                    init_time=now,
                    login_exp_time=None)
                db_session.add(record)
                response.set_cookie('session_id', record.id)
            if new_session['logged_in'] is not None:
                record.login_exp_time = now + datetime.timedelta(minutes=30)
            record.flash = to_string(new_session['flash'])
            db_session.commit()
            return response

        return inner

    return manage_session


def to_string(lis):
    i = []
    for x in lis:
        i.append(x[0])
        i.append(x[1])
    return '\n'.join(i)


def to_tup_list(string):
    if string == '':
        return []
    split = string.split('\n')
    result = []
    for i in range(0, len(split), 2):
        result.append((split[i], split[i + 1]))
    return result
