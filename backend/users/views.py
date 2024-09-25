from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.permissions import IsCurrentUser
from api.serializers import FollowSerializer, UserRecipeSerializer
from users.models import Follow
from users.paginations import UserRecipePagination
from users.serializers import AvatarSerializer

User = get_user_model()


class UserViewSet(BaseUserViewSet):
    """Представление для пользователей."""

    pagination_class = UserRecipePagination

    def get_permissions(self):
        if self.action in ('me', 'avatar'):
            return [IsAuthenticated(), IsCurrentUser(),]
        if self.action in ('subscriptions', 'subscribe'):
            return [IsAuthenticated(),]
        return super().get_permissions()

    @action(["put", "delete"], detail=False, url_path='me/avatar')
    def avatar(self, request, *args, **kwargs):
        user = request.user
        if request.method == "PUT":
            serializer = AvatarSerializer(
                user, data=request.data, context={'context': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(["get",], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        """Действие для получения пользователем подписок."""

        user = request.user
        followings_id = Follow.objects.filter(user=user).values_list(
            'following', flat=True
        )
        followings = [User.objects.get(id=id) for id in followings_id]
        page = self.paginate_queryset(followings)
        if page is not None:
            serializer = UserRecipeSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserRecipeSerializer(followings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(['post', 'delete',], detail=True,)
    def subscribe(self, request, *args, **kwargs):
        """Экшн для подписки."""

        id = kwargs.get('id')
        following = get_object_or_404(User, id=id)
        data = request.data
        data['id'] = id
        serializer = FollowSerializer(
            data=data, context={'request': request}
        )
        user = self.request.user
        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        follow = Follow.objects.filter(user=user, following=following)
        if follow.exists():
            follow.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'errors': 'Подписки не существует.'},
            status=status.HTTP_400_BAD_REQUEST
        )
