import datetime
from os import remove
from flask import render_template
from flask import make_response
from flask import current_app
from flask import Blueprint
from flask import redirect
from flask import url_for
from flask import session
from flask import request
from flask import jsonify
from flask import flash
from flask import abort
from flask import g

import sqlalchemy
import json

from app.model.helper import verifyPassword
from app.model import MapDataHistory
from app.model import MapData
from app.model import User
from app.shared import DB

from app.helper import random_public_id
from app.helper import fragment_parser
from app.helper import login

# debug
import pprint

public = Blueprint('public_controller', __name__)
DEBUG_PRINT = pprint.PrettyPrinter(indent=2)


# cookie and session fetch/set operation ---------->

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

# cookie and session fetch/set operation ---------->


# User login operation ---------->

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

                flash('Akun ditambahkan', 'info')
                return redirect(url_for('public_controller.public_login'))

            except (sqlalchemy.exc.IntegrityError):
                user.rollback()
                flash('Akun sudah terdaftar !', 'error')
                return render_template('register/index.html')

        elif '' in validator:
            flash('Pastikan isikan semua informasi !', 'error')
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
                        flash('Password salah', 'error')
                else:
                    flash('Akun tidak terdaftar', 'error')

            else:
                flash('Silahkan masukkan password !', 'error')
        else:
            flash('Silahkan masukkan username !', 'error')

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


# User login operation ---------->


# CRUD operation ---------->

@public.route('/')
@login
def public_index():
    map_list = MapData.query.filter(MapData.is_used == True).all()
    tower_serializer = []
    data_serializer = []

    for tower_item in map_list:
        tower_serializer.append({
            "id": tower_item.id,
            "tower_name": tower_item.tower_name,
            "latlang": json.loads(tower_item.latlang),
            "address": tower_item.address
        })

    for map_item in map_list:
        detailed_tower_info = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(MapDataHistory.tower_id == map_item.id)\
            .limit(5)\
            .all()

        data_serializer.append({
            "tower_id": f'tower${map_item.id}',
            "tower_name": map_item.tower_name,
            "public_id": random_public_id(),
            "latlang": json.loads(map_item.latlang),
            "desc": map_item.desc,
            "address": map_item.address,
            "isp_provider": map_item.isp_provider,
            "installation_date": map_item.installation_date,
            "is_used": map_item.is_used,
            "report": sorted([info[1].get() for info in detailed_tower_info], key=lambda i: i["report_date"], reverse=True)
        })

    return render_template(
        'home/index.html',
        user=g.user.username,
        map_list=data_serializer,
        tower_list=tower_serializer
    )


@public.route('/tower_list')
@login
def public_towerlist():
    page = request.args.get('page', 1, type=int)
    tower_list = MapData.query.filter(MapData.is_used == True).all()
    map_data = MapData.query.filter(MapData.is_used == True)\
        .paginate(page=page, per_page=10)

    data_serializers = []
    tower_serializers = []

    for tower_item in tower_list:
        tower_serializers.append({
            "id": tower_item.id,
            "tower_name": tower_item.tower_name,
            "latlang": json.loads(tower_item.latlang),
            "address": tower_item.address
        })

    for map_item in map_data.items:
        data_serializers.append({
            "tower_id": f'tower${map_item.id}',
            "tower_name": map_item.tower_name,
            "latlang": json.loads(map_item.latlang),
            "address": map_item.address,
            "isp_provider": map_item.isp_provider,
            "installation_date": map_item.installation_date,
        })

    return render_template(
        'tower_list/index.html',
        map_list=data_serializers,
        pagination=map_data,
        tower_list=tower_serializers
    )


@public.route('/tower_detail/<string:tower>')
@login
def public_tower_detail(tower):
    page = request.args.get('page', 1, type=int)
    tower_id = fragment_parser(tower).get('id')

    tower_list = MapData.query.filter(MapData.is_used == True).all()
    tower_serializers = []

    tower_raw = MapData.query.get(tower_id)
    history_data = MapDataHistory.query\
        .filter(MapDataHistory.tower_id == tower_raw.id)\
        .paginate(page=page, per_page=5)

    for tower_item in tower_list:
        tower_serializers.append({
            "id": tower_item.id,
            "tower_name": tower_item.tower_name,
            "latlang": json.loads(tower_item.latlang),
            "address": tower_item.address
        })

    tower_data = {
        "tower_id": f'tower#{tower_raw.id}',
        "tower_name": tower_raw.tower_name,
        "latlang": json.loads(tower_raw.latlang),
        "address": tower_raw.address,
        "desc": tower_raw.desc,
        "isp_provider": tower_raw.isp_provider,
    }

    return render_template(
        'tower_management/index.html',
        tower_detail=tower_data,
        tower_report=history_data,
        tower_list=tower_serializers
    )


@public.route('/add', methods=['GET', 'POST'])
@login
def public_add():
    if request.method == 'POST':
        try:
            latlang = json.dumps({
                "latitude": float(request.form.get('tower-latitude')),
                "longitude": float(request.form.get('tower-longitude'))
            })

            tower_name = request.form.get('tower-name')
            address = request.form.get('tower-address')
            isp_provider = request.form.get('tower-isp')
            desc = request.form.get('tower-desc')

            new_location = MapData(
                tower_name=tower_name,
                latlang=latlang,
                address=address,
                isp_provider=isp_provider,
                desc=desc
            )

            new_location.save()
            flash('lokasi tersimpan', 'success')
            return redirect(url_for('public_controller.public_towerlist'))

        except ValueError:
            flash('Maaf penulisan koordinat lokasi salah', 'error')
            return redirect(url_for('public_controller.public_towerlist'))

        except (sqlalchemy.exc.SQLAlchemyError):
            new_location.rollback()
            flash('Maaf, terjadi gangguan pada server !', 'error')
            return redirect(url_for('public_controller.public_towerlist'))

    return redirect(url_for('public_controller.public_towerlist'))


@public.route('/delete/<string:tower>', methods=['GET'])
@login
def public_delete_tower(tower):
    try:
        parsed_id = fragment_parser(tower).get('id')
        remove_tower = MapData.query.get(parsed_id)
        remove_tower.is_used = False
        remove_tower.save()
        flash('Titik tower dihapus !', 'info')

    except (sqlalchemy.exc.SQLAlchemyError):
        flash('Terjadi kesalahan saat menghapus titik tower', 'error')
        DB.session.rollback()
    return redirect(url_for('public_controller.public_towerlist'))


@public.route('/move-tower', methods=['GET', 'POST'])
@login
def public_move_tower():
    if request.method == 'GET':
        id_fragment = str(request.args['tower_id'])
        if id_fragment:
            tower_id = fragment_parser(id_fragment).get('id')
            tower = MapData.query.get(tower_id)
            data_serializer = {
                "latlng": json.loads(tower.latlang),
                "address": tower.address,
                "tower_id": tower_id
            }
            print(tower.address)
            return render_template('move/index.html', tower=data_serializer)

        else:
            abort(403)

    elif request.method == 'POST':
        tower_id = request.form.get('move-tower-id')
        new_address = request.form.get('tower-move-address')
        new_latitude = request.form.get('tower-move-latitude')
        new_longitude = request.form.get('tower-move-longitude')
        desc = request.form.get('tower-move-desc')

        try:
            tower = MapData.query.get(tower_id)
            tower.report.append(
                MapDataHistory(
                    report_date=datetime.datetime.now(),
                    status='perpindahan',
                    move_from=tower.latlang,
                    address_history=tower.address,
                    report_desc=desc
                )
            )
            tower.address = new_address
            tower.latlang = json.dumps({
                'latitude': new_latitude,
                'longitude': new_longitude
            })

            tower.save()

        except (sqlalchemy.exc.SQLAlchemyError) as Err:
            print(Err)

        return redirect(url_for('public_controller.public_index'))


@public.route('/report/<string:report_type>', methods=['GET', 'POST'])
@login
def public_report_damage(report_type):
    if request.method == 'POST':
        if report_type == 'damage':
            report_date = request.form.get('tower-damage-date')
            damage_report = request.form.get('tower-damage-description')
            tower_id = fragment_parser(
                request.form.get('tower-damage-coord')).get('id')

            try:
                tower = MapData.query.get(tower_id)
                tower.report.append(
                    MapDataHistory(
                        report_date=report_date,
                        report_desc=damage_report,
                        address_history=None,
                        status='kerusakan',
                        move_from=None
                    )
                )
                tower.save()
                flash('Laporan sudah disimpan', 'success')

            except (sqlalchemy.exc.SQLAlchemyError):
                tower.rollback()
                flash('Terjadi kesalahan saat menyimpan laporan', 'error')

        elif report_type == 'repr':
            report_date = request.form.get('tower-repair-date')
            repair_report = request.form.get('tower-repair-description')
            tower_id = fragment_parser(
                request.form.get('tower-repair-coord')).get('id')

            try:
                tower = MapData.query.get(tower_id)
                tower.report.append(
                    MapDataHistory(
                        report_date=report_date,
                        report_desc=repair_report,
                        address_history=None,
                        status='perbaikan',
                        move_from=None
                    )
                )
                tower.save()
                flash('Laporan sudah disimpan', 'success')

            except (sqlalchemy.exc.SQLAlchemyError):
                tower.rollback()
                flash('Terjadi kesalahan saat menyimpan laporan', 'error')

        else:
            abort(404)

    return redirect(url_for('public_controller.public_index'))


@public.route('/recap', methods=['GET', 'POST'])
@login
def public_data_recap():
    if request.method == 'GET':
        recap_type = request.args.get('type', None)
        map_list = MapData.query.all()
        tower_serializer = []
        for tower_item in map_list:
            tower_serializer.append({
                "id": tower_item.id,
                "latlang": json.loads(tower_item.latlang),
                "address": tower_item.address
            })

        if recap_type == 'error':
            return render_template(
                'recap/index.html',
                page_title="Rekap kerusakan",
                subtitle='Rekap daftar tower yang mengalami kerusakan',
                tower_list=tower_serializer
            )

        elif recap_type == 'repairement':
            return render_template(
                'recap/index.html',
                page_title="Rekap perbaikan",
                subtitle='Rekap daftar tower dalam perbaikan',
                tower_list=tower_serializer
            )

        elif recap_type == 'movement':
            return render_template(
                'recap/index.html',
                page_title="Rekap perpindahan",
                subtitle='Rekap daftar tower dipindahkan',
                tower_list=tower_serializer
            )

        elif recap_type == 'map-dl':
            return render_template(
                'recap/index.html',
                page_title="Download map",
                subtitle='Download map',
                tower_list=tower_serializer
            )

        elif recap_type == 'all':
            return render_template(
                'recap/index.html',
                page_title="Rekap keseluruhan",
                subtitle='Rekap data seluruh tower',
                tower_list=tower_serializer
            )

        else:
            return redirect(url_for('public_controller.public_index'))

    elif request.method == 'POST':
        test = request.get_json()
        print(test.get('endDate', None))
        return jsonify({
            "test": "result"
        })

    else:
        return redirect(url_for('public_controller.public_index'))


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


# CRUD operation ---------->


# Debug operation ---------->


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


# Debug operation ---------->
