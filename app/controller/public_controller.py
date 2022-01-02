import datetime
from flask import render_template
from flask import make_response
from flask import current_app
from flask import Blueprint
from flask import redirect
from flask import url_for
from flask import session
from flask import request
from flask import flash
from flask import g

import sqlalchemy
import json

from app.model.helper import verifyPassword
from app.model import MapData
from app.model import User

from app.helper import random_public_id

from app.helper import login

public = Blueprint('public_controller', __name__)


@public.before_app_request
def logged_in_user():
    if request.cookies.get('_remember') == 'remember':
        user_by_cookies = request.cookies.get('user_id')
        g.user = User.query.get(user_by_cookies)
        g.username = request.cookies.get('_username')
        g.remember = request.cookies.get('_remember')

    elif request.cookies.get('_remember') is None:
        user_by_session = session.get('user_id')
        if user_by_session is None:
            g.user = None
            g.remember = request.cookies.get('_remember')
        else:
            g.user = User.query.get(user_by_session)
            g.remember = request.cookies.get('_remember')
    else:
        g.user = None
        g.remember = request.cookies.get('_remember')


@public.route('/')
@login
def public_index():

    map_list = MapData.query.order_by(MapData.installation_date.desc()).all()
    data_serializer = []
    for map_item in map_list:
        data_serializer.append({
            "public_id": random_public_id(),
            "latlang": json.loads(map_item.latlang),
            "desc": map_item.desc,
            "address": map_item.address,
            "isp_provider": map_item.isp_provider,
            "installation_date": map_item.installation_date.isoformat(),
            "move_date": map_item.move_date,
            "damage_date": map_item.damage_date,
            "is_repaired": map_item.is_repaired,
            "is_moved": map_item.is_moved,
            "repair_report": map_item.repair_report,
            "damage_report": map_item.damage_report,
            "move_location": map_item.move_location,
        })
    print(data_serializer)
    return render_template('home/index.html', user=g.user.username, map_list=data_serializer)


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
            if is_admin == 'on':
                admin = True
            else:
                admin = False

            if is_active == 'on':
                active = True
            else:
                active = False

            try:
                user = User(username=username, password=password,
                            is_active=active, is_admin=admin)
                user.save()

                flash('user added', 'info')
                return redirect(url_for('public_controller.public_login'))

            except (sqlalchemy.exc.IntegrityError):
                user.rollback()
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
        rememberMe = request.form.get('rememberMe')

        if username:
            if password:
                user = User.query.filter(
                    User.username == username).one_or_none()

                if user:
                    verify = verifyPassword(user.password, password)

                    if verify:
                        if rememberMe == 'remember':
                            response = make_response(
                                redirect(
                                    url_for(
                                        'public_controller.public_index'
                                    )
                                )
                            )

                            response.set_cookie(
                                'user_id',
                                user.id,
                                max_age=current_app.config.get(
                                    'COOKIE_TIMEOUT'
                                )
                            )

                            response.set_cookie(
                                '_remember',
                                rememberMe,
                                max_age=current_app.config.get(
                                    'COOKIE_TIMEOUT'
                                )
                            )

                            response.set_cookie(
                                '_username',
                                username,
                                max_age=current_app.config.get(
                                    'COOKIE_TIMEOUT'
                                )
                            )

                            flash(f'welcome {username}', 'info')
                            return response
                        else:
                            response = redirect(
                                url_for(
                                    'public_controller.public_index'
                                )
                            )

                            session.clear()
                            session['user_id'] = user.id

                            response.delete_cookie('user_id')
                            response.delete_cookie('_remember')
                            response.delete_cookie('_username')

                            flash(f'welcome {username}', 'info')
                            return response
                    else:
                        flash('Password wrong', 'error')
                else:
                    flash('User not registered', 'error')

            else:
                flash('No password provided !', 'error')
        else:
            flash('No username provided !', 'error')

    elif request.method == 'GET':
        if g.user is not None:
            return redirect(url_for('public_controller.public_index'))

    return render_template('login/index.html')


@public.route('/logout')
@login
def public_logout():
    if g.remember == 'remember':
        response = make_response(
            redirect(
                url_for(
                    'public_controller.public_login'
                )
            )
        )

        response.delete_cookie('user_id')
        return response

    else:
        session.clear()
        flash(f'Bye {g.user.username}', 'info')
        return redirect(url_for('public_controller.public_login'))


@public.route('/add', methods=['GET', 'POST'])
@login
def public_add():
    if request.method == 'POST':
        try:
            latlang = json.dumps({
                "latitude": float(request.form.get('tower-latitude')),
                "longitude": float(request.form.get('tower-longitude'))
            })

            address = request.form.get('tower-address')
            isp_provider = request.form.get('tower-isp')
            installation_date = datetime.datetime.now()
            desc = request.form.get('tower-desc')
            is_repaired = False
            is_moved = False
            repair_report = None
            damage_report = None
            move_location = None
            damage_date = None
            move_date = None

            new_location = MapData(
                latlang=latlang,
                address=address,
                isp_provider=isp_provider,
                desc=desc,
                installation_date=installation_date,
                is_repaired=is_repaired,
                is_moved=is_moved,
                repair_report=repair_report,
                damage_report=damage_report,
                move_location=move_location,
                move_date=move_date,
                damage_date=damage_date
            )

            new_location.save()
            flash('lokasi tersimpan', 'success')
            return redirect(url_for('public_controller.public_index'))

        except ValueError:
            flash('Maaf penulisan koordinat lokasi salah', 'error')
            return render_template('home/index.html')

        except (sqlalchemy.exc.SQLAlchemyError):
            new_location.rollback()
            flash('maaf, terjadi gangguan pada server !', 'error')
            return render_template('home/index.html')

    return render_template('home/index.html')


@public.route('/help')
@login
def public_help():
    return render_template('help/index.html')
