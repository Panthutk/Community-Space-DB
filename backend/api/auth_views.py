# backend/api/auth_views.py
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import User
from .serializers import UserSerializer
from .jwt_utils import generate_token, decode_token


class RegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        data = request.data.copy()
        password = data.get("password")
        if not password:
            return Response({"password": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)

        # put hashed password into password_hash before serializer
        data["password_hash"] = make_password(password)
        data.pop("password", None)

        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            token = generate_token(user.id)
            return Response({"user": serializer.data, "token": token}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        """
        Accepts either:
        - email + password
        - username (name) + password
        Backwards-compatible with older frontend that used `username`, and newer one using `email`.

        If stored password_hash is plain text and equals provided password, accept it ONCE and replace with a proper hash.
        """
        # Accept multiple identifier keys for compatibility
        identifier = request.data.get("email") or request.data.get(
            "username") or request.data.get("name")
        password = request.data.get("password")

        if not identifier or not password:
            return Response({"detail": "Provide email/username and password."}, status=status.HTTP_400_BAD_REQUEST)

        # Try to find the user by email first, then by name
        user = None
        try:
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(name=identifier)
            except User.DoesNotExist:
                return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        stored = user.password_hash or ""

        # 1) If stored value is a proper Django hash, check it normally
        try:
            if check_password(password, stored):
                token = generate_token(user.id)
                serializer = UserSerializer(user)
                return Response({"user": serializer.data, "token": token})
        except Exception:
            # In case stored value is malformed for check_password (rare), continue to fallback
            pass

        # 2) Fallback migration: if stored equals the raw password (i.e. stored as plaintext),
        #    accept and immediately re-hash & save a proper hashed password for future logins.
        if stored == password:
            user.password_hash = make_password(password)
            user.save(update_fields=["password_hash"])
            token = generate_token(user.id)
            serializer = UserSerializer(user)
            return Response({"user": serializer.data, "token": token})

        # otherwise unauthorized
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


class MeView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
        token = auth.split(" ", 1)[1].strip()
        payload = decode_token(token)
        if not payload:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_401_UNAUTHORIZED)
        user_id = payload.get("user_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Invalid token."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserSerializer(user)
        return Response(serializer.data)
