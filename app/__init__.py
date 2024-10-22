from flask import Flask
from flask_migrate import Migrate

from .controller import public_controller
from .controller import error_handler
# from .shared import LMANAGER
from .shared import CSRF
from .shared import DB

# from .model import User
# from .model import *


def init_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_pyfile('./config/config.py')

    DB.init_app(app)
    CSRF.init_app(app)
    Migrate().init_app(app=app, db=DB)

    # route / controller
    app.register_blueprint(public_controller.public)
    app.register_blueprint(error_handler.error_controller)

    return app
