from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение на полный доступ авторам.
    Для всех остальных доступ на чтение.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_authenticated and obj.author == request.user
        )


class IsCurrentUser(permissions.BasePermission):
    """Разрешение на доступ только самому пользователю."""

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and obj.pk == request.user.pk


class IsSelfUserOrReadOnly(permissions.BasePermission):
    """
    Разрешение на полный доступ самому пользователю.
    Для всех остальных доступ на чтение.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_authenticated and obj == request.user
        )


class ReadOnly(permissions.BasePermission):
    """Разрешение на чтение для всех."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS
