from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username
