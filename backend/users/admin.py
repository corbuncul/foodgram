from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import Follow

User = get_user_model()

admin.site.empty_value_display = '-пусто-'


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
    search_fields = ('username', 'email',)
    ordering = ('username',)


admin.site.register(User, UserAdmin)
admin.site.register(Follow)
