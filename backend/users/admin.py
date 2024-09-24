from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import Follow

User = get_user_model()

admin.site.empty_value_display = '-пусто-'


class UserAdmin(BaseUserAdmin):
    """Кастомный админ для модели User с дополнительными полями."""

    list_display = (
        'pk',
        'username',
        'first_name',
        'last_name',
        'email',
        'avatar',
    )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': (
            'first_name', 'last_name', 'email', 'avatar')}),
        ('Permissions', {'fields': (
            'is_active', 'is_staff', 'is_superuser', 'groups',
            'user_permissions'
        )}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions')


admin.site.register(User, UserAdmin)
admin.site.register(Follow)
