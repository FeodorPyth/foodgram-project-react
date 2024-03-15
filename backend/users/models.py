from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from foodgram.constants import LENGTH_FOR_EMAIL, LENGTH_FOR_USERNAME
from .validators import validate_username_me


class User(AbstractUser):
    """Кастомная модель пользователей."""
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        max_length=LENGTH_FOR_USERNAME,
        blank=True,
        unique=True,
        help_text=(
            'Необходимое поле. 150 символов или меньше.'
            'Только буквы, цифры и @/./+/-/_.'
        ),
        validators=[username_validator, validate_username_me],
        verbose_name='Имя пользователя',
    )
    email = models.EmailField(
        max_length=LENGTH_FOR_EMAIL,
        unique=True,
        verbose_name='Адрес электронной почты'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
        'password'
    ]

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'username'],
                name='unique_email_and_username'
            )
        ]

    def __str__(self):
        return self.username
