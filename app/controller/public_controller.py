from crypt import methods
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
# from os import remove
import datetime

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

# controller view filter ---------->


@public.app_template_filter()
def parse_coords_latitude(context):
    latitude = json.loads(context).get('latitude')
    return latitude


@public.app_template_filter()
def parse_coords_longitude(context):
    longitude = json.loads(context).get('longitude')
    return longitude


@public.app_template_filter()
def parse_coords_to_json(context):
    parser = json.dumps(context)
    return parser

# controller view filter ---------->


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
    search_tower = request.args.get('tower_name', None)
    tower_list = MapData.query.filter(MapData.is_used == True).all()

    data_serializers = []
    tower_serializers = []

    for tower_item in tower_list:
        tower_serializers.append({
            "id": tower_item.id,
            "tower_name": tower_item.tower_name,
            "latlang": json.loads(tower_item.latlang),
            "address": tower_item.address
        })

    if (search_tower):
        tower = MapData.query.filter(
            MapData.tower_name.contains(search_tower),
            MapData.is_used == True
        )\
            .paginate(page=page, per_page=10)

        if (tower):
            for map_item in tower.items:
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
                pagination=tower,
                tower_list=tower_serializers
            )

    else:
        map_data = MapData.query.filter(MapData.is_used == True)\
            .paginate(page=page, per_page=10)

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
            tower_name = request.form.get('tower-damage-coord')

            try:
                tower = MapData.query.filter(
                    MapData.is_used == True,
                    MapData.tower_name == tower_name
                )\
                    .first()

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
            tower_name = request.form.get('tower-damage-coord')

            try:

                tower = MapData.query.filter(
                    MapData.is_used == True,
                    MapData.tower_name == tower_name
                )\
                    .first()

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


@public.route('/kerusakan', methods=['GET', 'POST'])
@login
def public_damage():
    PAGE_LIMIT = 10
    tower_name = request.args.get('tower-name', None)
    tower_list = MapData.query.filter(MapData.is_used == True).all()
    filter_date_start = request.args.get('date-start', None)
    filter_date_end = request.args.get('date-end', None)
    page = request.args.get('page', 1, type=int)

    tower_serializers = []
    filter = None

    for tower_item in tower_list:
        tower_serializers.append({
            "id": tower_item.id,
            "tower_name": tower_item.tower_name,
            "latlang": json.loads(tower_item.latlang),
            "address": tower_item.address
        })

    data = DB.session.query(MapData, MapDataHistory)\
        .join(MapDataHistory)\
        .filter(
            MapData.is_used == True,
            MapDataHistory.status == 'kerusakan')\
        .order_by(MapDataHistory.report_date.desc())\
        .paginate(page=page, per_page=10)

    if (filter_date_start is not None and filter_date_end is not None):
        converted_start_date = datetime.datetime.strptime(
            filter_date_start,
            "%Y-%m-%d"
        )

        converted_end_date = datetime.datetime.strptime(
            filter_date_end,
            "%Y-%m-%d"
        )

        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(
                MapData.is_used == True,
                MapData.tower_name.contains(tower_name),
                MapDataHistory.status == 'kerusakan',
                MapDataHistory.report_date >= converted_start_date,
                MapDataHistory.report_date <= converted_end_date)\
            .order_by(MapDataHistory.report_date.desc())\
            .paginate(page=page, per_page=10)

        filter = {
            'start_date': filter_date_start,
            'end_date': filter_date_end,
            'tower_name': tower_name
        }

    return render_template(
        'recap/damage.html',
        report_lists=data,
        filters=filter,
        tower_list=tower_serializers
    )


@public.route('/kerusakan/print')
@login
def public_damage_print():
    filters = request.args.get('filters')

    if filters != 'none':
        parsed_filter = json.loads(filters)

        date_start = datetime.datetime.strptime(
            parsed_filter.get('start_date'),
            "%Y-%m-%d"
        )

        date_end = datetime.datetime.strptime(
            parsed_filter.get('end_date'),
            "%Y-%m-%d"
        )

        time_spans = {
            'start_date': date_start,
            'end_date': date_end
        }

        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(
                MapData.is_used == True,
                MapData.tower_name.contains(parsed_filter.get('tower_name')),
                MapDataHistory.status == 'kerusakan',
                MapDataHistory.report_date >= date_start,
                MapDataHistory.report_date <= date_end)\
            .order_by(MapDataHistory.report_date.desc())\
            .all()

    elif filters == 'none':
        time_spans = 'none'
        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(
                MapData.is_used == True,
                MapDataHistory.status == 'kerusakan')\
            .order_by(MapDataHistory.report_date.desc())\
            .all()

    return render_template(
        'recap/print/damage_print.html',
        report_data=data,
        time_spans=time_spans
    )


@public.route('/perbaikan', methods=['GET', 'POST'])
@login
def public_repairement():
    PAGE_LIMIT = 10
    tower_name = request.args.get('tower-name', None)
    tower_list = MapData.query.filter(MapData.is_used == True).all()
    filter_date_start = request.args.get('date-start', None)
    filter_date_end = request.args.get('date-end', None)
    page = request.args.get('page', 1, type=int)

    tower_serializers = []
    filter = None

    for tower_item in tower_list:
        tower_serializers.append({
            "id": tower_item.id,
            "tower_name": tower_item.tower_name,
            "latlang": json.loads(tower_item.latlang),
            "address": tower_item.address
        })

    data = DB.session.query(MapData, MapDataHistory)\
        .join(MapDataHistory)\
        .filter(
            MapData.is_used == True,
            MapDataHistory.status == 'perbaikan')\
        .order_by(MapDataHistory.report_date.desc())\
        .paginate(page=page, per_page=10)

    if (filter_date_start is not None and filter_date_end is not None):
        converted_start_date = datetime.datetime.strptime(
            filter_date_start,
            "%Y-%m-%d"
        )

        converted_end_date = datetime.datetime.strptime(
            filter_date_end,
            "%Y-%m-%d"
        )

        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(
                MapData.is_used == True,
                MapData.tower_name.contains(tower_name),
                MapDataHistory.status == 'perbaikan',
                MapDataHistory.report_date >= converted_start_date,
                MapDataHistory.report_date <= converted_end_date)\
            .order_by(MapDataHistory.report_date.desc())\
            .paginate(page=page, per_page=10)

        filter = {
            'start_date': filter_date_start,
            'end_date': filter_date_end,
            'tower_name': tower_name

        }

    return render_template(
        'recap/repairement.html',
        report_lists=data,
        filters=filter,
        tower_list=tower_serializers
    )


@public.route('/perbaikan/print')
@login
def public_repairement_print():
    filters = request.args.get('filters')

    if filters != 'none':
        parsed_filter = json.loads(filters)

        date_start = datetime.datetime.strptime(
            parsed_filter.get('start_date'),
            "%Y-%m-%d"
        )

        date_end = datetime.datetime.strptime(
            parsed_filter.get('end_date'),
            "%Y-%m-%d"
        )

        time_spans = {
            'start_date': date_start,
            'end_date': date_end
        }

        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(
                MapData.is_used == True,
                MapData.tower_name.contains(parsed_filter.get('tower_name')),
                MapDataHistory.status == 'perbaikan',
                MapDataHistory.report_date >= date_start,
                MapDataHistory.report_date <= date_end)\
            .order_by(MapDataHistory.report_date.desc())\
            .all()

    elif filters == 'none':
        time_spans = 'none'
        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(
                MapData.is_used == True,
                MapDataHistory.status == 'perbaikan')\
            .order_by(MapDataHistory.report_date.desc())\
            .all()

    return render_template(
        'recap/print/repairement_print.html',
        report_data=data,
        time_spans=time_spans
    )


@public.route('/perpindahan', methods=['GET', 'POST'])
@login
def public_moved():
    PAGE_LIMIT = 10
    tower_name = request.args.get('tower-name', None)
    tower_list = MapData.query.filter(MapData.is_used == True).all()
    filter_date_start = request.args.get('date-start', None)
    filter_date_end = request.args.get('date-end', None)
    page = request.args.get('page', 1, type=int)

    tower_serializers = []
    filter = None

    for tower_item in tower_list:
        tower_serializers.append({
            "id": tower_item.id,
            "tower_name": tower_item.tower_name,
            "latlang": json.loads(tower_item.latlang),
            "address": tower_item.address
        })

    data = DB.session.query(MapData, MapDataHistory)\
        .join(MapDataHistory)\
        .filter(
            MapData.is_used == True,
            MapDataHistory.status == 'perpindahan')\
        .order_by(MapDataHistory.report_date.desc())\
        .paginate(page=page, per_page=10)

    if (filter_date_start is not None and filter_date_end is not None):
        converted_start_date = datetime.datetime.strptime(
            filter_date_start,
            "%Y-%m-%d"
        )

        converted_end_date = datetime.datetime.strptime(
            filter_date_end,
            "%Y-%m-%d"
        )

        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(
                MapData.is_used == True,
                MapData.tower_name.contains(tower_name),
                MapDataHistory.status == 'perpindahan',
                MapDataHistory.report_date >= converted_start_date,
                MapDataHistory.report_date <= converted_end_date)\
            .order_by(MapDataHistory.report_date.desc())\
            .paginate(page=page, per_page=10)

        filter = {
            'start_date': filter_date_start,
            'end_date': filter_date_end,
            'tower_name': tower_name
        }

    return render_template(
        'recap/moved.html',
        report_lists=data,
        filters=filter,
        tower_list=tower_serializers
    )


@public.route('/perpindahan/print')
@login
def public_moved_print():
    filters = request.args.get('filters')

    if filters != 'none':
        parsed_filter = json.loads(filters)

        date_start = datetime.datetime.strptime(
            parsed_filter.get('start_date'),
            "%Y-%m-%d"
        )

        date_end = datetime.datetime.strptime(
            parsed_filter.get('end_date'),
            "%Y-%m-%d"
        )

        time_spans = {
            'start_date': date_start,
            'end_date': date_end
        }

        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(
                MapData.is_used == True,
                MapData.tower_name.contains(parsed_filter.get('tower_name')),
                MapDataHistory.status == 'perpindahan',
                MapDataHistory.report_date >= date_start,
                MapDataHistory.report_date <= date_end)\
            .order_by(MapDataHistory.report_date.desc())\
            .all()

    elif filters == 'none':
        time_spans = 'none'
        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(
                MapData.is_used == True,
                MapDataHistory.status == 'perpindahan')\
            .order_by(MapDataHistory.report_date.desc())\
            .all()

    return render_template(
        'recap/print/moved_print.html',
        report_data=data,
        time_spans=time_spans
    )


@public.route('/report', methods=['GET', 'POST'])
@login
def public_report():
    PAGE_LIMIT = 10
    tower_name = request.args.get('tower-name')
    tower_list = MapData.query.filter(MapData.is_used == True).all()
    filter_date_start = request.args.get('date-start', None)
    filter_date_end = request.args.get('date-end', None)
    page = request.args.get('page', 1, type=int)

    tower_serializers = []
    filter = None

    for tower_item in tower_list:
        tower_serializers.append({
            "id": tower_item.id,
            "tower_name": tower_item.tower_name,
            "latlang": json.loads(tower_item.latlang),
            "address": tower_item.address
        })

    data = DB.session.query(MapData, MapDataHistory)\
        .join(MapDataHistory)\
        .filter(MapData.is_used == True)\
        .order_by(MapDataHistory.report_date.desc())\
        .paginate(page=page, per_page=10)

    if (filter_date_start is not None and filter_date_end is not None):
        converted_start_date = datetime.datetime.strptime(
            filter_date_start,
            "%Y-%m-%d"
        )

        converted_end_date = datetime.datetime.strptime(
            filter_date_end,
            "%Y-%m-%d"
        )

        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(
                MapData.is_used == True,
                MapData.tower_name.contains(tower_name),
                MapDataHistory.report_date >= converted_start_date,
                MapDataHistory.report_date <= converted_end_date)\
            .order_by(MapDataHistory.report_date.desc())\
            .paginate(page=page, per_page=10)

        filter = {
            'start_date': filter_date_start,
            'end_date': filter_date_end,
            'tower_name': tower_name
        }

    return render_template(
        'recap/report.html',
        report_lists=data,
        filters=filter,
        tower_list=tower_serializers
    )


@public.route('/laporan/print')
@login
def public_report_print():
    filters = request.args.get('filters')

    if filters != 'none':
        parsed_filter = json.loads(filters)

        date_start = datetime.datetime.strptime(
            parsed_filter.get('start_date'),
            "%Y-%m-%d"
        )

        date_end = datetime.datetime.strptime(
            parsed_filter.get('end_date'),
            "%Y-%m-%d"
        )

        time_spans = {
            'start_date': date_start,
            'end_date': date_end
        }

        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(
                MapData.is_used == True,
                MapData.tower_name.contains(parsed_filter.get('tower_name')),
                MapDataHistory.report_date >= date_start,
                MapDataHistory.report_date <= date_end)\
            .order_by(MapDataHistory.report_date.desc())\
            .all()

    elif filters == 'none':
        time_spans = 'none'
        data = DB.session.query(MapData, MapDataHistory)\
            .join(MapDataHistory)\
            .filter(MapData.is_used == True)\
            .order_by(MapDataHistory.report_date.desc())\
            .all()

    return render_template(
        'recap/print/report_print.html',
        report_data=data,
        time_spans=time_spans
    )


@public.route('/download_map')
@login
def public_download_map():
    tower_list = MapData.query.filter(MapData.is_used == True).all()
    tower_serializers = []
    data_serializers = []

    for tower_item in tower_list:
        data_serializers.append({})

        tower_serializers.append({
            "id": tower_item.id,
            "tower_name": tower_item.tower_name,
            "latlang": json.loads(tower_item.latlang),
            "address": tower_item.address
        })
    return render_template(
        'recap/dl-map.html',
        tower_list=tower_serializers,

    )


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
