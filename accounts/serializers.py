"""
Equivalent of the `publicUser()` helper in auth.service.js, plus thin
input serializers (the JS controller read straight off req.body; these
just give us the same fields with DRF-native parsing).
"""
from rest_framework import serializers


def public_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "isGuest": user.is_guest,
        "emailVerified": user.email_verified,
        "phoneVerified": user.phone_verified,
    }


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)


class RequestOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, allow_blank=True)


class VerifyOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(required=False, allow_blank=True)
    code = serializers.CharField(required=False, allow_blank=True)


class GuestLoginSerializer(serializers.Serializer):
    deviceId = serializers.CharField(required=False, allow_blank=True)


class UpgradeGuestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True, trim_whitespace=False)
    phone = serializers.CharField(required=False, allow_blank=True)


class RefreshSerializer(serializers.Serializer):
    refreshToken = serializers.CharField(required=False, allow_blank=True)


class LogoutSerializer(serializers.Serializer):
    refreshToken = serializers.CharField(required=False, allow_blank=True)
