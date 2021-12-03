from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

DB = SQLAlchemy()
CSRF = CSRFProtect()
