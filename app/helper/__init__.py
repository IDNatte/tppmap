from flask import redirect
from flask import url_for
from flask import g
import functools
import random
import string


def login(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('public_controller.public_login'))

        return view(**kwargs)

    return wrapped_view


def random_public_id():
    """
    Public string randomizer
    """
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(10))
