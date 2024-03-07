from django.contrib import admin

from .models import User


class UserAdmin(admin.ModelAdmin):
    """Кастомный класс для регистрации модели пользователей в админке."""
    list_display = ('username', 'email',)
    search_fields = ('email', 'username',)
    list_filter = ('email', 'username',)


admin.site.register(User, UserAdmin)
