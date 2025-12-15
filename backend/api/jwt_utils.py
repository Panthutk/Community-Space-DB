import jwt
from datetime import datetime, timedelta
from django.conf import settings

JWT_ALGORITHM = "HS256"
JWT_LIFETIME_MINUTES = 60


def generate_token(user_id):
    now = datetime.utcnow()
    payload = {
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=JWT_LIFETIME_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token):
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
