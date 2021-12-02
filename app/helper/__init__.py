from flask import redirect
from flask import url_for
from flask import g
import functools


def login(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('public_controller.public_login'))

        return view(**kwargs)

    return wrapped_view
