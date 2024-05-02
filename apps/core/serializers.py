from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from rest_framework import serializers as sr

User = get_user_model()


def validate_email_address(value: str) -> str:
    """
        Validates an email address.
        Parameters:
            value (str): The email address to be validated.
        Returns:
            str: The validated email address
    """

    try:
        validate_email(value)
    except sr.ValidationError:
        raise sr.ValidationError("Invalid email address.")
    return value


class RegisterSerializer(sr.Serializer):
    full_name = sr.CharField()
    username = sr.CharField()
    email = sr.CharField(validators=[validate_email_address])
    referral = sr.CharField(required=False, allow_blank=True)
    password = sr.CharField(write_only=True)


class VerifyEmailSerializer(sr.Serializer):
    email = sr.CharField(validators=[validate_email_address])
    otp = sr.IntegerField()


class ResendEmailVerificationCodeSerializer(sr.Serializer):
    email = sr.CharField(validators=[validate_email_address])


class SendNewEmailVerificationCodeSerializer(sr.Serializer):
    email = sr.CharField(validators=[validate_email_address])


class ChangeEmailSerializer(sr.Serializer):
    email = sr.CharField(validators=[validate_email_address])
    otp = sr.IntegerField()


class ProfileSerializer(sr.Serializer):
    user = sr.HiddenField(default=sr.CurrentUserDefault())
    user_id = sr.UUIDField(read_only=True)
    id = sr.UUIDField(read_only=True)
    full_name = sr.CharField(source="user.full_name")
    username = sr.CharField(source="user.username")
    date_of_birth = sr.DateField()
    email = sr.EmailField(source="user.email", read_only=True)
    avatar = sr.ImageField()
    referral_code = sr.CharField(source="user.referral_code", read_only=True)
    followers = sr.IntegerField(read_only=True)
    tokens = sr.IntegerField(read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        for field_name, field_value in data.items():
            if field_value is None:
                data[field_name] = ""

        return data

    def update(self, instance, validated_data):
        user = instance.user

        for key, value in validated_data.items():
            if key != 'user':  # Exclude the 'user' field
                setattr(instance, key, value)

        # Handle the 'user' field separately
        user_data = validated_data.get('user')
        if user_data:
            for key, value in user_data.items():
                setattr(instance.user, key, value)

        user.save()
        instance.save()
        return instance


class LoginSerializer(sr.Serializer):
    email_or_username = sr.CharField(required=True)
    password = sr.CharField(write_only=True)


class ChangePasswordSerializer(sr.Serializer):
    password = sr.CharField(max_length=50, min_length=6, write_only=True)


class RequestNewPasswordCodeSerializer(sr.Serializer):
    email = sr.CharField(validators=[validate_email_address])
