from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .jwt_utils import decode_token
from .models import User


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        print("User model:", User)
        print("User count:", User.objects.count())

        auth = request.headers.get("Authorization", "")

        if not auth.startswith("Bearer "):
            return None

        token = auth.split(" ", 1)[1].strip()
        payload = decode_token(token)

        if not payload:
            raise AuthenticationFailed("Invalid or expired token.")

        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationFailed("Invalid token payload.")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found.")

        return (user, None)
