from django.conf import settings
from django.core.mail import send_mail


def send_transactional_email(to_email, subject, html, text):
    if getattr(settings, 'EMAIL_PROVIDER', 'console') == 'resend':
        import resend

        if not settings.RESEND_API_KEY:
            raise RuntimeError('RESEND_API_KEY is required when EMAIL_PROVIDER=resend.')

        resend.api_key = settings.RESEND_API_KEY
        return resend.Emails.send({
            'from': settings.RESEND_FROM_EMAIL,
            'to': [to_email],
            'subject': subject,
            'html': html,
            'text': text,
        })

    return send_mail(
        subject=subject,
        message=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        html_message=html,
        fail_silently=False,
    )


def send_verification_email(user, verification_url):
    subject = 'Verify your TeleSec email'
    text = (
        f'Hi {user.first_name or user.username},\n\n'
        'Please verify your TeleSec account before signing in:\n'
        f'{verification_url}\n\n'
        'If you did not create this account, you can ignore this email.'
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.6;color:#0f172a">
      <h2>Verify your TeleSec email</h2>
      <p>Hi {user.first_name or user.username},</p>
      <p>Please verify your TeleSec account before signing in.</p>
      <p>
        <a href="{verification_url}" style="display:inline-block;background:#41bf63;color:#020617;
        padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:700">
          Verify email
        </a>
      </p>
      <p>If the button does not work, copy this link:</p>
      <p><a href="{verification_url}">{verification_url}</a></p>
      <p>If you did not create this account, you can ignore this email.</p>
    </div>
    """
    return send_transactional_email(user.email, subject, html, text)


def send_password_reset_email(user, reset_url):
    subject = 'Reset your TeleSec password'
    text = (
        f'Hi {user.first_name or user.username},\n\n'
        'Use this link to reset your TeleSec password:\n'
        f'{reset_url}\n\n'
        'If you did not request a password reset, you can ignore this email.'
    )
    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.6;color:#0f172a">
      <h2>Reset your TeleSec password</h2>
      <p>Hi {user.first_name or user.username},</p>
      <p>Use this link to reset your TeleSec password.</p>
      <p>
        <a href="{reset_url}" style="display:inline-block;background:#41bf63;color:#020617;
        padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:700">
          Reset password
        </a>
      </p>
      <p>If the button does not work, copy this link:</p>
      <p><a href="{reset_url}">{reset_url}</a></p>
      <p>If you did not request a password reset, you can ignore this email.</p>
    </div>
    """
    return send_transactional_email(user.email, subject, html, text)
