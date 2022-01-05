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
from app.model import MapDataHistory
from app.model import MapData
from app.model import User
from app.shared import DB

from app.helper import random_public_id
from app.helper import login

# debug
import pprint

public = Blueprint('public_controller', __name__)
DEBUG_PRINT = pprint.PrettyPrinter(indent=2)


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

    map_list = MapData.query.all()
    tower_serializer = []
    data_serializer = []

    for tower_item in map_list:
        tower_serializer.append({
            "id": tower_item.id,
            "latlang": json.loads(tower_item.latlang),
            "address": tower_item.address
        })

    for map_item in map_list:
        detailed_tower_info = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(MapDataHistory.tower_id == map_item.id)\
            .all()

        data_serializer.append({
            "public_id": random_public_id(),
            "latlang": json.loads(map_item.latlang),
            "desc": map_item.desc,
            "address": map_item.address,
            "isp_provider": map_item.isp_provider,
            "installation_date": map_item.installation_date,
            "report": sorted([info[1].get() for info in detailed_tower_info], key=lambda i: i["report_date"], reverse=True)
        })

    print(tower_serializer)

    return render_template(
        'home/index.html',
        user=g.user.username,
        map_list=data_serializer,
        tower_list=tower_serializer
    )


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
            desc = request.form.get('tower-desc')

            new_location = MapData(
                latlang=latlang,
                address=address,
                isp_provider=isp_provider,
                desc=desc
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


@public.route('/check-location')
@login
def public_check_location():
    lat = request.args.get('lat', None)
    lang = request.args.get('lng', None)

    if (lat is not None and lang is not None):
        latlang = {
            "latitude": lat,
            "longitude": lang
        }
        return render_template('get_location/index.html', latlang=latlang)
    else:
        flash('Lokasi tidak valid', 'error')
        return redirect(url_for('public_controller.public_index'))


@public.route('/debug')
@login
def public_debug():
    debugData = MapData.query.get(
        "_6g)%CHMqyqI?{|#||n%sVA)C8TB;x6MIL1T1p\,J*PpsAwk'I"
    )

    loremData = "Lorem ipsum dolor sit amet consectetur adipisicing elit. Est, unde rem.\
        Dignissimos id ducimus adipisci amet nulla possimus fugit rerum, illo vel distinctio\
        sunt ratione a esse cum odio omnis quam voluptatem, incidunt dolores? Natus ducimus\
        quod, consequuntur voluptatem quasi error, soluta possimus voluptate accusantium porro\
        reprehenderit sequi rem sunt eos iusto sint quo voluptates nemo et, deserunt quae? Facere,\
        distinctio sequi quisquam laborum corrupti expedita sint fugit laboriosam mollitia voluptates\
        nulla voluptas modi accusantium repellat dignissimos ea, excepturi iusto unde veniam cupiditate.\
        Distinctio perferendis tempora quibusdam doloremque labore accusantium velit, et laudantium. Porro\
        ad a commodi cumque, quasi fugit maiores reiciendis inventore! Odit, fugiat saepe. Ad minus\
        repellendus dolorum modi rerum quis quidem, ipsam vitae sint in necessitatibus excepturi, maxime\
        totam iste sapiente commodi impedit unde aperiam hic, culpa non. Tempora deleniti tempore iste quam\
        enim sint. Dolor accusantium, sunt atque nam praesentium, reiciendis pariatur culpa asperiores\
        cupiditate ipsa animi porro beatae illum quae odit. Rerum autem fugit soluta quibusdam quam eos\
        provident nam ea, saepe, corporis excepturi? Sequi praesentium tenetur recusandae fuga, dicta ipsa.\
        Aliquam iure, porro sapiente, aspernatur voluptatibus animi nostrum, cumque sunt sint doloremque\
        laborum hic totam. Beatae, maxime. Sunt obcaecati, quo eum nobis suscipit similique!"

    debugData.report.append(
        MapDataHistory(
            report_date=datetime.datetime.now(),
            status="perpindahan",
            report_desc=loremData,
            move_from=json.dumps({
                "latitude": "-2.9348426",
                "longitude": "115.1660467"
            })
        )
        # MapDataHistory(
        #     report_date=datetime.datetime.now(),
        #     status="perbaikan",
        #     report_desc=loremData,
        #     move_from=None
        # )
    )

    debugData.save()
    return redirect(url_for('public_controller.public_index'))
