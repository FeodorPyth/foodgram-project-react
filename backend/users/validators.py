from django.core.exceptions import ValidationError

from foodgram.constants import URL_PATH_NAME


def validate_username_me(value):
    """
    Валидация поля username.
    Значение не должно быть равно 'me'.
    """
    if value == URL_PATH_NAME:
        raise ValidationError(f'Нельзя использовать {URL_PATH_NAME}'
                              ' в качестве имени пользователя.')
    return value
