from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Business, User


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ["id", "name", "join_code", "timezone", "max_hours_per_week", "min_rest_hours"]
        read_only_fields = ["id", "join_code"]

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise serializers.ValidationError("Enter a valid timezone, for example Asia/Kolkata.")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        is_manager = request is not None and request.user.is_authenticated and request.user.role == User.Role.MANAGER
        if not is_manager:
            data.pop("join_code")
        return data


class UserSerializer(serializers.ModelSerializer):
    business = BusinessSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "email", "role", "business"]


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["name", "email", "password", "role"]

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class JoinSerializer(serializers.Serializer):
    join_code = serializers.CharField(max_length=8)

    def validate_join_code(self, value):
        try:
            return Business.objects.get(join_code=value.strip().upper())
        except Business.DoesNotExist:
            raise serializers.ValidationError("This join code does not match any business.")


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "role"]
