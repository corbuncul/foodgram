from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models.query import QuerySet
from django.http import HttpRequest

from users.models import Follow, User

admin.site.empty_value_display = '-пусто-'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админ для модели User с дополнительными полями."""

    list_display = (
        'pk',
        'username',
        'first_name',
        'last_name',
        'email',
        'avatar',
    )
    list_display_links = [
        'username',
        'email'
    ]
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    ordering = ('username',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):


    list_display = (
        'user',
        'following',
    )
    list_display_links = (
        'user',
        'following',
    )
    search_fields = (
        'user__username',
        'following__username',
    )
    list_filter = (
        'user',
        'following',
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        return qs.select_related('user', 'following')
