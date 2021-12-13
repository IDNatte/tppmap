from flask import render_template
from flask import Blueprint

error_controller = Blueprint('error_endpoint', __name__)


@error_controller.app_errorhandler(401)
@error_controller.app_errorhandler(403)
@error_controller.app_errorhandler(404)
def error_4xx(error):
    return render_template('error/4xx.html', msg=error), error.code


@error_controller.app_errorhandler(500)
def error_5xx(error):
    return render_template('error/5xx.html', msg=error), error.code
