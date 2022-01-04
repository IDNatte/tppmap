from app.model.helper import random_id_generator
from app.model.helper import passwordHash
from app.shared import DB

import datetime


class User(DB.Model):
    __tablename__ = "User"

    id = DB.Column(
        DB.String(255),
        primary_key=True,
        nullable=False,
        default=random_id_generator
    )

    username = DB.Column(DB.String(200), nullable=False, unique=True)
    password = DB.Column(DB.String(255), nullable=False, unique=True)
    is_admin = DB.Column(DB.Boolean, nullable=False, default=False)
    is_active = DB.Column(DB.Boolean, nullable=False, default=True)

    def __init__(self, username, password, is_admin, is_active):
        self.username = username
        self.password = passwordHash(password)
        self.is_admin = is_admin
        self.is_active = is_active

    def save(self):
        DB.session.add(self)
        DB.session.commit()

    def rollback(self):
        DB.session.rollback()

    def update(self):
        DB.session.commit()

    def delete(self):
        DB.session.delete(self)
        DB.session.commit()

    def get(self):
        return {
            'username': self.username,
            'is_admin': self.is_admin,
            'is_active': self.is_active
        }


class MapData(DB.Model):
    __tablename__ = "map_data"

    id = DB.Column(
        DB.String(255),
        primary_key=True,
        nullable=False,
        default=random_id_generator
    )

    latlang = DB.Column(DB.JSON, nullable=False)
    desc = DB.Column(DB.Text, nullable=True)
    address = DB.Column(DB.Text, nullable=False)
    isp_provider = DB.Column(DB.String(200), nullable=False)
    installation_date = DB.Column(DB.DateTime, default=datetime.datetime.now)
    report = DB.relationship(
        'MapDataHistory',
        backref='MapData',
        cascade='all, delete-orphan',
        order_by="desc(MapDataHistory.report_date)"
    )

    def __init__(self,
                 latlang,
                 address,
                 isp_provider,
                 desc):
        self.latlang = latlang
        self.address = address,
        self.isp_provider = isp_provider
        self.desc = desc

    def save(self):
        DB.session.add(self)
        DB.session.commit()

    def update(self):
        DB.session.commit()

    def delete(self):
        DB.session.delete(self)
        DB.session.commit()

    def rollback(self):
        DB.session.rollback()

    def get(self):
        return {
            'id': self.id,
            'latlang': self.latlang,
            'desc': self.desc,
            'address': self.address,
            'isp_provider': self.isp_provider,
        }


class MapDataHistory(DB.Model):
    __tablename__ = "map_data_history"

    id = DB.Column(
        DB.String(255),
        primary_key=True,
        nullable=False,
        default=random_id_generator
    )

    tower_id = DB.Column(
        DB.String(255),
        DB.ForeignKey('map_data.id')
    )

    report_date = DB.Column(DB.DateTime, nullable=False)
    status = DB.Column(DB.String(150), default=False)
    move_from = DB.Column(DB.JSON)
    report_desc = DB.Column(DB.Text)

    def __init__(self,
                 report_date,
                 status,
                 report_desc,
                 move_from):
        self.status = status
        self.report_date = report_date
        self.report_desc = report_desc
        self.move_from = move_from

    def get(self):
        return {
            "status": self.status,
            "report_date": self.report_date,
            "report_desc": self.report_desc,
            "move_from": self.move_from
        }
