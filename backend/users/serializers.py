"""
users/serializers.py
Serializers for registration, login response, and profile
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    # FIX: full_name is required at model level but wasn't enforced here —
    # empty submissions would hit a DB NOT NULL error instead of a clean API error.
    full_name = serializers.CharField(required=True, max_length=200)
    # FIX: username explicitly required so missing username gives a clear error
    username  = serializers.CharField(required=True, max_length=80)

    class Meta:
        model  = User
        fields = [
            'username', 'password', 'email', 'mobile', 'full_name',
            'date_of_birth', 'gender', 'category', 'marital_status',
            'aadhaar', 'income_range', 'occupation', 'state', 'has_land',
            'father_name', 'mother_name', 'family_size', 'profile_pic',
        ]

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate_aadhaar(self, value):
        if value:
            digits = value.replace(' ', '').replace('-', '')
            if not digits.isdigit() or len(digits) != 12:
                raise serializers.ValidationError('Aadhaar must be exactly 12 digits.')
            return digits
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSummarySerializer(serializers.ModelSerializer):
    """Minimal user info returned in JWT login response"""
    class Meta:
        model  = User
        fields = ['id', 'username', 'full_name', 'email', 'is_admin',
                  'category', 'occupation', 'state', 'income_range', 'profile_pic']
        read_only_fields = ['id', 'is_admin']


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'mobile', 'full_name',
            'date_of_birth', 'gender', 'category', 'marital_status',
            'aadhaar', 'income_range', 'occupation', 'state', 'has_land',
            'father_name', 'mother_name', 'family_size',
            'profile_pic', 'is_admin', 'date_joined',
        ]
        read_only_fields = ['id', 'is_admin', 'date_joined']
