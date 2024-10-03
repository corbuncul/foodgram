from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from recipes import constants


class User(AbstractUser):
    """Пользователь.

    Модель пользователя на основе AbstractUser.
    Поля модели:
        email: Email пользователя.
        username: Имя пользователя.
        first_name: Имя.
        last_name: Фамилия.
        avatar: Аватар.
    """

    email = models.EmailField(
        max_length=constants.EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='Электронная почта пользователя',
        help_text='Введите свой электронный адрес',
        error_messages={
            'unique': 'Пользователь с таким email уже существует.',
        },
    )
    username = models.CharField(
        max_length=constants.NAME_MAX_LENGTH,
        unique=True,
        help_text=(
            'Обязательное поле. 150 символов или меньше. '
            f'Только буквы, цифры и {constants.USERNAME_CHECK} символы.'
        ),
        validators=[
            RegexValidator(
                regex=constants.USERNAME_CHECK,
                message=(
                    'Имя пользователя может содержать только '
                    f'буквы, цифры и {constants.USERNAME_CHECK} символы.'
                ),
            ),
        ],
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
        verbose_name='Имя пользователя',
    )
    first_name = models.CharField(max_length=constants.NAME_MAX_LENGTH)
    last_name = models.CharField(max_length=constants.NAME_MAX_LENGTH)
    avatar = models.ImageField(
        'аватар', upload_to='users/', blank=True, null=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)
        constraints = (
            models.UniqueConstraint(
                fields=('username', 'email'), name='unique_username_email'
            ),
        )

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Подписки пользователей.

    Модель для хранения связи Подписчик - Респондент.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='followers',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Респондент',
        related_name='followings',
    )

    class Meta:
        unique_together = ('user', 'following')
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} -> {self.following.username}'

    def clean(self):
        if self.user == self.following:
            raise ValidationError('Подписка на самого себя запрещена!')
