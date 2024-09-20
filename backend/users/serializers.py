import base64

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from djoser.serializers import UserSerializer as BaseUserSerializer

from users.models import Follow


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле для загрузки изображений в формате base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserSerializer(BaseUserSerializer):
    """Сериализатор для пользователей."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, following):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Follow.objects.filter(user=user, following=following).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления автара"""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class FollowSerializer(serializers.ModelSerializer):
    """Сериалайзер для подписок."""

    id = serializers.IntegerField(source='following.id')

    class Meta:
        model = Follow
        fields = ('id',)

    def validate(self, data):
        user = self.context['request'].user
        id = data['following']['id']
        following = get_object_or_404(User, id=id)
        follow = Follow.objects.filter(user=user, following=following)
        if self.context['request'].method == 'DELETE' and not follow.exists():
            raise serializers.ValidationError('Подписки не существует.')
        if user == following:
            raise serializers.ValidationError(
                'Подписка на самого себя запрещена.'
            )
        if follow.exists():
            raise serializers.ValidationError(
                'Подписка уже существует.'
            )
        data['user'] = user
        return super().validate(data)

    def create(self, validated_data):
        following = User.objects.get(id=validated_data['following']['id'])
        user = validated_data['user']
        Follow.objects.create(following=following, user=user)
        return following

    def to_representation(self, instance):
        request = self.context['request']
        return UserRecipeSerializer(
            instance, context={'request': request}
        ).data
