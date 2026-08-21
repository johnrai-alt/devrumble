"""
Equivalent of auth.controller.js + auth.service.js combined (Django/DRF
doesn't need a separate repository layer for simple ORM lookups the way
the JS project split routes -> controller -> service -> repository, but
the logic below is a line-for-line port of auth.service.js).
"""
from django.conf import settings
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import bcrypt

from .exceptions import AppError
from .models import OtpCode, RefreshToken, User
from .otp import generate_otp, hash_otp, otp_expiry, send_otp_sms
from .serializers import public_user
from .throttling import OtpRequestThrottle
from .tokens import generate_refresh_token, hash_token, sign_access_token

BCRYPT_ROUNDS = settings.BCRYPT_ROUNDS


def _bcrypt_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(BCRYPT_ROUNDS)).decode()


def _bcrypt_compare(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def _issue_token_pair(user: User) -> dict:
    access_token = sign_access_token(user)
    token, token_hash, expires_at = generate_refresh_token()
    RefreshToken.objects.create(user=user, token_hash=token_hash, expires_at=expires_at)
    return {"accessToken": access_token, "refreshToken": token}


class RegisterView(APIView):
    def post(self, request):
        data = request.data
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise AppError("email and password are required", 400)
        if len(password) < 8:
            raise AppError("password must be at least 8 characters", 400)
        if User.objects.filter(email=email).exists():
            raise AppError("An account with this email already exists", 409)

        password_hash = _bcrypt_hash(password)
        user = User.objects.create(email=email, password_hash=password_hash, is_guest=False)
        # TODO: send verification email here
        tokens = _issue_token_pair(user)
        return Response({"user": public_user(user), **tokens}, status=201)


class LoginView(APIView):
    def post(self, request):
        data = request.data
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise AppError("email and password are required", 400)

        user = User.objects.filter(email=email).first()
        if not user or not user.password_hash:
            raise AppError("Invalid email or password", 401)
        if not _bcrypt_compare(password, user.password_hash):
            raise AppError("Invalid email or password", 401)

        tokens = _issue_token_pair(user)
        return Response({"user": public_user(user), **tokens})


class RequestOtpView(APIView):
    throttle_classes = [OtpRequestThrottle]

    def post(self, request):
        data = request.data
        phone = data.get("phone")

        if not phone:
            raise AppError("phone is required", 400)

        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        recent_count = OtpCode.objects.filter(phone=phone, created_at__gt=one_hour_ago).count()
        if recent_count >= 3:
            raise AppError("Too many OTP requests. Try again later.", 429)

        code = generate_otp()
        OtpCode.objects.create(phone=phone, code_hash=hash_otp(code), expires_at=otp_expiry())

        try:
            send_otp_sms(phone, code)
        except Exception:
            raise AppError("Failed to send SMS. Please try again.", 502)

        return Response({"message": "OTP sent"})


class VerifyOtpView(APIView):
    def post(self, request):
        data = request.data
        phone = data.get("phone")
        code = data.get("code")

        if not phone or not code:
            raise AppError("phone and code are required", 400)

        otp = (
            OtpCode.objects.filter(phone=phone, consumed=False, expires_at__gt=timezone.now())
            .order_by("-created_at")
            .first()
        )
        if not otp:
            raise AppError("No valid OTP found. Please request a new one.", 400)
        if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
            raise AppError("Too many incorrect attempts. Request a new code.", 429)
        if hash_otp(code) != otp.code_hash:
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            raise AppError("Incorrect code", 401)

        otp.consumed = True
        otp.save(update_fields=["consumed"])

        user = User.objects.filter(phone=phone).first()
        if not user:
            user = User.objects.create(phone=phone, is_guest=False, phone_verified=True)
        elif not user.phone_verified:
            user.phone_verified = True
            user.save(update_fields=["phone_verified"])

        tokens = _issue_token_pair(user)
        return Response({"user": public_user(user), **tokens})


class GuestLoginView(APIView):
    def post(self, request):
        data = request.data
        device_id = data.get("deviceId")

        if not device_id:
            raise AppError("deviceId is required", 400)

        user = User.objects.filter(device_id=device_id).first()
        if not user:
            user = User.objects.create(device_id=device_id, is_guest=True)

        tokens = _issue_token_pair(user)
        return Response({"user": public_user(user), **tokens})


class UpgradeGuestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_user = request.user  # TokenUser: sub, is_guest, ...
        data = request.data
        email = data.get("email")
        password = data.get("password")
        phone = data.get("phone")

        if not current_user.is_guest:
            raise AppError("This account is not a guest account", 400)
        if not email and not phone:
            raise AppError("email or phone is required to upgrade", 400)

        user = User.objects.get(pk=current_user.sub)
        user.is_guest = False

        if email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                raise AppError("Email already in use", 409)
            user.email = email
        if password:
            user.password_hash = _bcrypt_hash(password)
        if phone:
            if User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
                raise AppError("Phone already in use", 409)
            user.phone = phone

        user.save()
        tokens = _issue_token_pair(user)  # re-issue: is_guest changed
        return Response({"user": public_user(user), **tokens})


class RefreshView(APIView):
    def post(self, request):
        data = request.data
        refresh_token = data.get("refreshToken")

        if not refresh_token:
            raise AppError("refreshToken is required", 400)

        token_hash = hash_token(refresh_token)
        stored = RefreshToken.objects.filter(
            token_hash=token_hash, revoked=False, expires_at__gt=timezone.now()
        ).first()
        if not stored:
            raise AppError("Invalid or expired refresh token", 401)

        stored.revoked = True  # rotate
        stored.save(update_fields=["revoked"])

        user = User.objects.filter(pk=stored.user_id).first()
        if not user:
            raise AppError("User no longer exists", 401)

        tokens = _issue_token_pair(user)
        return Response({"user": public_user(user), **tokens})


class LogoutView(APIView):
    def post(self, request):
        data = request.data
        refresh_token = data.get("refreshToken")

        if not refresh_token:
            raise AppError("refreshToken is required", 400)

        RefreshToken.objects.filter(token_hash=hash_token(refresh_token)).update(revoked=True)
        return Response({"message": "Logged out"})


class LogoutAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        RefreshToken.objects.filter(user_id=request.user.sub, revoked=False).update(revoked=True)
        return Response({"message": "All sessions revoked"})


class MeView(APIView):
    """
    Backs the User Profile screen: GET reads the logged-in user, PATCH
    lets them edit email/phone/password. Not present in the original JS
    project (no /me route existed), added since the UI needs it.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.get(pk=request.user.sub)
        return Response(public_user(user))

    def patch(self, request):
        user = User.objects.get(pk=request.user.sub)
        data = request.data

        email = data.get("email")
        password = data.get("password")
        phone = data.get("phone")

        if email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                raise AppError("Email already in use", 409)
            user.email = email
        if password:
            if len(password) < 8:
                raise AppError("password must be at least 8 characters", 400)
            user.password_hash = _bcrypt_hash(password)
        if phone:
            if User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
                raise AppError("Phone already in use", 409)
            user.phone = phone

        user.save()
        return Response(public_user(user))
