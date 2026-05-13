from django.conf import settings
from django.db import transaction
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer
from .email_service import send_password_reset_email, send_verification_email
from .tokens import email_verification_token

User = get_user_model()


def build_user_token_url(user, path, token_generator, frontend_url=None):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = token_generator.make_token(user)
    frontend_url = frontend_url or getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    return f'{frontend_url}{path}?uid={uid}&token={token}'


def send_user_verification_email(user, frontend_url=None):
    if user.user_type != 'root':
        return

    verification_url = build_user_token_url(user, '/verify-email', email_verification_token, frontend_url)
    send_verification_email(user, verification_url)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                user = serializer.save()
                send_user_verification_email(user, request.headers.get('Origin'))
        except Exception as exc:
            detail = 'Account could not be created because the verification email could not be sent.'
            if settings.DEBUG:
                detail = f'{detail} Email error: {exc}'

            return Response(
                {'detail': detail},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class VerifyEmailView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')

        if not uid or not token:
            return Response(
                {'detail': 'Verification link is missing required information.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Verification link is invalid or expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_verified:
            return Response({'detail': 'Email is already verified.'})

        if not email_verification_token.check_token(user, token):
            return Response(
                {'detail': 'Verification link is invalid or expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_verified = True
        user.save(update_fields=['is_verified'])
        return Response({'detail': 'Email verified successfully. You can now sign in.'})


class ForgotPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        generic_message = {'detail': 'If this email exists, a reset link has been sent.'}

        if not email:
            return Response(generic_message)

        user = User.objects.filter(email__iexact=email).first()
        if user:
            try:
                reset_url = build_user_token_url(
                    user,
                    '/reset-password',
                    email_verification_token,
                    request.headers.get('Origin'),
                )
                send_password_reset_email(user, reset_url)
            except Exception as exc:
                detail = 'Unable to send reset email right now. Please try again later.'
                if settings.DEBUG:
                    detail = f'{detail} Email error: {exc}'

                return Response(
                    {'detail': detail},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return Response(generic_message)


class ResetPasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        password = request.data.get('password')

        if not uid or not token or not password:
            return Response(
                {'detail': 'Reset link and new password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(password) < 8:
            return Response(
                {'password': 'Password must be at least 8 characters long.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Reset link is invalid or expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not email_verification_token.check_token(user, token):
            return Response(
                {'detail': 'Reset link is invalid or expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        user.save(update_fields=['password'])
        return Response({'detail': 'Password reset successfully. You can now sign in.'})

class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user
