"""
Table/column names here mirror exactly what auth.repository.js assumed
(and the original README's note to "coordinate with the DB team"):
users, otp_codes, refresh_tokens.
"""
from django.db import models


class User(models.Model):
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=32, unique=True, null=True, blank=True)
    device_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    password_hash = models.CharField(max_length=255, null=True, blank=True)
    is_guest = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email or self.phone or self.device_id or f"user#{self.pk}"


class OtpCode(models.Model):
    phone = models.CharField(max_length=32, db_index=True)
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    consumed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_codes"

    def __str__(self):
        return f"otp for {self.phone}"


class RefreshToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="refresh_tokens")
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "refresh_tokens"

    def __str__(self):
        return f"refresh token for user#{self.user_id}"
