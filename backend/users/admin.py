from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    """Кастомный класс для регистрации модели пользователей в админке."""
    list_display = ('username', 'email',)
    search_fields = ('email', 'username',)
    list_filter = ('email', 'username',)
