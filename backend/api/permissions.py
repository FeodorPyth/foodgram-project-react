from rest_framework import permissions


class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Кастомный класс пермишена.
    Неавторизованным пользователям разрешёно только чтение данных.
    Администраторам и авторам записей доступны остальные методы.
    """
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or (obj.author == request.user
                    or request.user.is_superuser))
