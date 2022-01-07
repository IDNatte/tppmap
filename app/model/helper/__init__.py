import random
import string

from argon2.exceptions import VerifyMismatchError
from argon2 import PasswordHasher


def random_id_generator():
    return ''.join(
        (random.choice(
            string.ascii_letters + string.digits
        ) for x in range(50)
        )
    )


def passwordHash(string):
    hasher = PasswordHasher()
    hashPass = hasher.hash(string)
    return str(hashPass)


def verifyPassword(hash, string):
    try:
        hasher = PasswordHasher()
        verifPass = hasher.verify(hash, string)
        return verifPass

    except (VerifyMismatchError):
        return False
