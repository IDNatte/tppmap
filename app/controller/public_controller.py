from werkzeug.utils import redirect
from flask import render_template
from flask import Blueprint
from flask import url_for
from flask import session
from flask import request
from flask import flash
from flask import g
import sqlalchemy

from app.model.helper import verifyPassword
from app.model import User

from app.helper import login

public = Blueprint('public_controller', __name__)


@public.before_app_request
def logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)


@public.route('/')
@login
def public_index():
    return render_template('home/index.html')


@public.route('/register', methods=['GET', 'POST'])
def public_register():
    if request.method == 'GET':
        user = User.query.filter_by(is_admin=True).all()
        if (len(user) >= 1):
            return redirect(url_for('public_controller.public_login'))
        return render_template('register/index.html')

    if request.method == 'POST':
        username = request.form.get('username', default=None)
        password = request.form.get('password', default=None)
        is_admin = request.form.get('is_admin', default=None)
        is_active = request.form.get('is_active', default=None)

        validator = [username, password, is_admin, is_active]

        if '' not in validator:
            if is_admin == 'true':
                admin = True
            elif is_admin == 'false':
                admin = False

            if is_active == 'true':
                active = True
            elif is_active == 'false':
                active = False

            try:
                user = User(username=username, password=password,
                            is_active=active, is_admin=admin)
                user.save()

                flash('user added', 'info')
                return redirect(url_for('public_controller.public_login'))

            except (sqlalchemy.exc.IntegrityError):
                flash('user already registered !', 'error')
                return render_template('register/index.html')

        elif '' in validator:
            flash('please fill all detail', 'error')
            return render_template('register/index.html')


@public.route('/login', methods=['GET', 'POST'])
def public_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username:
            if password:
                user = User.query.filter(
                    User.username == username).one_or_none()

                if user:
                    verify = verifyPassword(user.password, password)

                    if verify:
                        session.clear()
                        session['user_id'] = user.id
                        flash('welcome', 'info')
                        return redirect(
                            url_for('public_controller.public_index')
                        )
                    else:
                        flash('Password wrong', 'error')
                else:
                    flash('User not registered', 'error')

            else:
                flash('No password provided !', 'error')
        else:
            flash('No username provided !', 'error')

    return render_template('login/index.html')


@public.route('/logout')
@login
def logout():
    session.clear()
    flash(f'Bye {g.user.username}', 'info')
    return redirect(url_for('public_controller.public_login'))
