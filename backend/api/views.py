import io
import csv
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
# from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import (
    UpdateModelMixin, DestroyModelMixin, CreateModelMixin
)
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, SAFE_METHODS
)
from rest_framework.response import Response

from api.constants import SHOPPING_CART_FILE_HEADERS
from api.serializers import (
    AvatarSerializer, DownloadShoppingCartSerializer, IngredientSerializer,
    AmountSerializer, FavoriteSerializer, TagSerializer, RecipeReadSerializer,
    RecipeWriteSerializer, ShoppingCartSerializer, UserSerializer, UserRecipeSerializer, FollowSerializer
)
from api.models import (
    Favorites, Ingredient, Recipe, ShoppingCart, Tag
)
from api.permissions import IsAuthorOrReadOnly, IsSelfUserOrReadOnly, ReadOnly
from users.models import Follow


User = get_user_model()


class SubscribeViewSet(viewsets.ModelViewSet):
    """Представление для подписки пользователей."""

    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    http_method_names = ('get', 'post', 'delete',)
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserRecipeSerializer
        return FollowSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(
        detail=True, methods=['post', 'delete',],
    )
    def subscribe(self, request, id=None):
        """Экшн для подписки."""

        following = get_object_or_404(User, id=id)
        data = request.data
        data['id'] = id
        serializer = self.get_serializer(
            data=data, context={'request': request}
        )
        user = self.request.user
        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        follow = self.get_queryset().filter(following=following)
        if follow.exists():
            follow.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'errors': 'Подписки не существует.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True, methods=['get',],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        user = request.user
        followings_id = Follow.objects.filter(user=user).values_list(
            'following', flat=True
        )
        followings = [User.objects.get(id=id) for id in followings_id]
        serializer = self.get_serializer(followings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ModelViewSet):
    """Представление тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    http_method_names = ('get',)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Представление ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    http_method_names = ('get',)
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    search_param = 'name'


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = [DjangoFilterBackend,]
    filterset_fields = [
        'is_favorited', 'author', 'is_in_shopping_cart', 'tags__slug',
    ]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        return super().perform_create(serializer)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [ReadOnly(),]
        if self.action == 'create':
            return [IsAuthenticated(),]
        return [IsAuthorOrReadOnly(),]


class AvatarUpdateDeleteViewSet(
    viewsets.GenericViewSet, UpdateModelMixin, DestroyModelMixin
):
    """Представление для обновления/удаления аватара пользователя."""

    serializer_class = AvatarSerializer
    permission_classes = (IsAuthenticated, IsSelfUserOrReadOnly,)

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        instance.avatar = None
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddDeleteRecipeShoppingCartViewSet(
    viewsets.GenericViewSet, CreateModelMixin, DestroyModelMixin
):
    """Представление для добавления/удаления рецепта в/из список(а) покупок."""

    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('post', 'delete',)

    def get_object(self):
        return get_object_or_404(
            ShoppingCart, user=self.request.user, recipe=get_object_or_404(
                Recipe, id=self.kwargs.get('id')
            )
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, id=self.kwargs.get('id'))
        return super().perform_create(serializer)

    def perform_destroy(self, instance):
        # obj = self.get_object()
        # obj.delete()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddDeleteRecipeToFavoriteViewSet(
    viewsets.GenericViewSet, CreateModelMixin, DestroyModelMixin
):
    """Представление для добавления/удаления рецепта в/из избранное(ого)."""

    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('post', 'delete',)

    def get_object(self):
        return get_object_or_404(
            Favorites, user=self.request.user, recipe=get_object_or_404(
                Recipe, id=self.kwargs.get('id')
            )
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, id=self.kwargs.get('id'))
        return super().perform_create(serializer)

    def perform_destroy(self, instance):
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DownloadView(viewsets.ViewSet):
    """Представление для скачивания файла покупок."""

    queryset = ShoppingCart.objects.all()
    serializer_class = DownloadShoppingCartSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).values(
            'recipe__ingredients__ingredient__name',
            'recipe__ingredients__ingredient__measurement_unit'
        ).annotate(sum=Sum('recipe__ingredients__amount'))

    @action(
        detail=False, methods=['get',],
        url_name='download_shopping_cart'
    )
    def download(self, request):
        """Action для скачивания файла списка покупок."""
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)

        csv_buffer = io.StringIO()
        csv_writer = csv.DictWriter(
            csv_buffer,
            fieldnames=SHOPPING_CART_FILE_HEADERS,
            extrasaction='ignore'
        )
        csv_writer.writeheader()

        for ingredient in serializer.data:
            csv_writer.writerow(ingredient)

        return HttpResponse(
            csv_buffer.getvalue(),
            headers={
                'Content-Disposition':
                'attachment; filename="Shopping_cart.csv"',
                'Accept': 'text/csv'
            },
            content_type='text/csv'
        )
