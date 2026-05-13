from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

PERSONAL_EMAIL_DOMAINS = {
    'gmail.com',
    'googlemail.com',
    'yahoo.com',
    'ymail.com',
    'rocketmail.com',
    'outlook.com',
    'hotmail.com',
    'live.com',
    'msn.com',
    'icloud.com',
    'me.com',
    'mac.com',
    'aol.com',
    'proton.me',
    'protonmail.com',
    'zoho.com',
    'yandex.com',
    'mail.com',
    'gmx.com',
    'rediffmail.com',
}


def is_personal_email(email):
    domain = email.rsplit('@', 1)[-1].strip().lower() if '@' in email else ''
    return domain in PERSONAL_EMAIL_DOMAINS

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'user_type', 'company_name', 'first_name', 'last_name')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'user_type', 'company_name', 'full_name')

    def validate(self, attrs):
        user_type = attrs.get('user_type', 'root')
        email = attrs.get('email', '')

        if user_type == 'iam' and is_personal_email(email):
            raise serializers.ValidationError({
                'email': 'IAM users must use a company email address. Personal emails like Gmail, Yahoo, and Outlook are not allowed.'
            })

        return attrs

    def create(self, validated_data):
        full_name = validated_data.pop('full_name', '')
        first_name = ''
        last_name = ''
        if full_name:
            parts = full_name.split(' ', 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            user_type=validated_data.get('user_type', 'root'),
            company_name=validated_data.get('company_name', ''),
            first_name=first_name,
            last_name=last_name
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        requested_user_type = self.initial_data.get('user_type')
        username = self.initial_data.get(self.username_field, '')

        if requested_user_type == 'iam' and is_personal_email(username):
            raise serializers.ValidationError({
                'username': 'IAM users must sign in with a company email address. Personal emails like Gmail, Yahoo, and Outlook are not allowed.'
            })

        data = super().validate(attrs)

        if self.user.user_type == 'iam' and is_personal_email(self.user.email):
            raise serializers.ValidationError({
                'username': 'IAM users must sign in with a company email address.'
            })

        if self.user.user_type == 'root' and not self.user.is_verified:
            raise AuthenticationFailed('Please verify your email first.')

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['user_type'] = user.user_type
        token['email'] = user.email
        return token
