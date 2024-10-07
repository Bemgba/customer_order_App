import datetime

import jwt

from config import ApplicationConfig


class JwtClient:

    @staticmethod
    def encode(user_id):
        payload = {
            'id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(
                minutes=ApplicationConfig.JWT_TOKEN_EXPIRES_IN_MINUTES),
            'iat': datetime.datetime.utcnow()
        }

        return jwt.encode(payload, ApplicationConfig.SECRET_KEY, algorithm="HS256")

    @staticmethod
    def decode(token):
        try:
            return jwt.decode(token, ApplicationConfig.SECRET_KEY, algorithms=['HS256'])

        except jwt.ExpiredSignatureError:
            return None