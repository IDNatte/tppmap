from enum import unique
from app.model.helper import random_id_generator
from app.model.helper import passwordHash
from app.shared import DB
import datetime


class User(DB.Model):
    __tablename__ = "User"

    id = DB.Column(DB.String(255), primary_key=True,
                   nullable=False, default=random_id_generator)
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

    id = DB.Column(DB.String(255), primary_key=True,
                   nullable=False, default=random_id_generator)
    latlang = DB.Column(DB.JSON, nullable=False)
    desc = DB.Column(DB.Text, nullable=True)
    address = DB.Column(DB.Text, nullable=False)
    isp_provider = DB.Column(DB.String(200), nullable=False)
    installation_date = DB.Column(DB.DateTime, default=datetime.datetime.now)
    move_date = DB.Column(DB.DateTime)
    damage_date = DB.Column(DB.DateTime)
    is_repaired = DB.Column(DB.Boolean, default=False)
    is_moved = DB.Column(DB.Boolean, default=False)
    repair_report = DB.Column(DB.Text)
    damage_report = DB.Column(DB.Text)
    move_location = DB.Column(DB.Text)

    def __init__(self,
                 latlang,
                 address,
                 isp_provider,
                 desc,
                 installation_date,
                 move_date,
                 damage_date,
                 is_repaired,
                 is_moved,
                 repair_report,
                 damage_report,
                 move_location):
        self.latlang = latlang
        self.address = address,
        self.isp_provider = isp_provider
        self.desc = desc
        self.installation_date = installation_date
        self.move_date = move_date
        self.damage_date = damage_date
        self.is_repaired = is_repaired
        self.is_moved = is_moved
        self.repair_report = repair_report
        self.damage_report = damage_report
        self.move_location = move_location

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
            'installation': self.installation_date,
            'damage': {
                'damageReport': self.damage_report,
                'damageDate': self.damage_date,
            },
            'repair': {
                'status': self.is_repaired,
                'repairReport': self.repair_report,
            },
            'move': {
                'status': self.is_moved,
                'movedDate': self.move_date,
                'location': self.move_location
            }
        }
