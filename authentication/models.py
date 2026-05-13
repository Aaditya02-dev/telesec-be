from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('root', 'Root User'),
        ('iam', 'IAM User'),
    )
    
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='root')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    # Use email as the primary login field for root users
    # But for IAM users, username might be used.
    # For simplicity, we'll keep email as unique.
    
    def __str__(self):
        return self.email
