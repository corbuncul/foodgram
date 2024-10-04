import csv
import io

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from djoser.views import UserViewSet as BaseUserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter, RecipeTagFilter
from api.mixins import MultiSerializerMixin
from api.paginations import UserRecipePagination
from api.permissions import IsAuthorOrReadOnly, IsCurrentUser, ReadOnly
from api.serializers import (
    AvatarSerializer,
    DownloadShoppingCartSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeShortSerializer,
    TagSerializer,
    UserRecipeSerializer,
)
from recipes.constants import SHOPPING_CART_FILE_HEADERS
from recipes.models import Favorites, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Follow

User = get_user_model()


class UserViewSet(BaseUserViewSet):
    """Основные деиствия с учетной записью пользователя.

    Помимо стандартных действий с учетной записью, таких как регистрация новых
    пользователей, изменение пароля или учетных данных (возможности
    унаследованы от родительского класса), добавляет возможность добавить или
    удалить аватар пользователя (метод avatar), оформить подписку на другого
    пользователя или отписаться от него (метод subscribe), получить список
    всех текущих подписок пользователя (метод subscriptions).
    """

    pagination_class = UserRecipePagination

    def get_queryset(self):
        return User.objects.all()

    def get_permissions(self):
        if self.action in ('me', 'avatar'):
            return [IsAuthenticated(), IsCurrentUser()]
        if self.action in ('subscriptions', 'subscribe'):
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(['put', 'delete'], detail=False, url_path='me/avatar')
    def avatar(self, request, *args, **kwargs):
        """Добавление и удаление автарки пользователя."""
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user, data=request.data, context={'context': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['get'], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        """Получение пользователем всех подписок."""
        followings = (
            User.objects.prefetch_related('followings__following__recipes')
            .filter(followings__user=request.user)
            .annotate(
                recipes_count=Count('followings__following__recipes'),
            )
        )
        page = self.paginate_queryset(followings)
        if page is not None:
            serializer = UserRecipeSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserRecipeSerializer(followings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(['post', 'delete'], detail=True)
    def subscribe(self, request, *args, **kwargs):
        """Создание и удаление подписок пользователей."""
        user = self.request.user
        if request.method == 'POST':
            following = get_object_or_404(
                User.objects.prefetch_related('recipes').annotate(
                    recipes_count=Count('recipes')
                ),
                id=kwargs.get('id'),
            )
            if user == following:
                return Response(
                    {'errors': 'Подписка на самого себя запрещена.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            follow, created = Follow.objects.get_or_create(
                user=user, following=following
            )
            if not created:
                return Response(
                    {'errors': 'Подписка уже существует.}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = UserRecipeSerializer(
                following, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, st = Follow.objects.filter(
            user=user, following_id=kwargs.get('id')
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Подписки не существует.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение списка тегов.

    Позволяет получить список всех тегов, имеющихся в базе
    одним списком.
    Доступно всем пользователям.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение списка ингредиентов.

    Позволяет получить список всех инредиентов, имеющихся в базе
    одним списком. Имеется возможность поиска по имени.
    Поиск производится по частичному вхождению в начале названия ингредиента.
    Доступно всем пользователям.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filterset_class = IngredientFilter


class RecipeViewSet(MultiSerializerMixin, viewsets.ModelViewSet):
    """Рецепты.

    Предоставляет возможность получить список рецептов
    или отдельно взятый рецепт, а также получить короткую
    ссылку на рецепт всем пользователям.
    Доступна фильтрация по избранному, автору, списку покупок и тегам.
    Для зарегистрированных пользователей имеется возможность создавать,
    редактировать и удалять свои рецепты. Также зарегистрированные
    пользователи могут добавлять или удалять рецепты в избранное или
    в список покупок.
    """

    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'ingredients'
    )
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_class = None
    serializer_class = RecipeWriteSerializer
    serializer_classes = {
        'shopping_cart': RecipeShortSerializer,
        'favorite': RecipeShortSerializer,
        'list': RecipeReadSerializer,
        'retrieve': RecipeReadSerializer,
        'create': RecipeWriteSerializer,
        'update': RecipeWriteSerializer,
    }

    def get_queryset(self):
        if self.request.user.is_authenticated:
            self.filterset_class = RecipeFilter
        else:
            self.filterset_class = RecipeTagFilter
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        return super().perform_create(serializer)

    def get_permissions(self):
        if self.action in ('list', 'get_link'):
            return [ReadOnly()]
        if self.action in ('create', 'shopping_cart', 'favorite'):
            return [IsAuthenticated()]
        return [IsAuthorOrReadOnly()]

    @action(
        ['post', 'delete'],
        detail=True,
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, *args, **kwargs):
        """Добавление рецепта в список покупок и удаления оттуда."""
        user = request.user
        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))
            shopping_cart, created = ShoppingCart.objects.get_or_create(
                recipe=recipe, user=user
            )
            if not created:
                return Response(
                    {'detail': 'Рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = self.get_serializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, state = ShoppingCart.objects.filter(
            recipe_id=kwargs.get('pk'), user=user
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепта нет в списке покупок.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        ['post', 'delete'],
        detail=True,
        url_path='favorite',
    )
    def favorite(self, request, *args, **kwargs):
        """Добавление рецепта в избранное и удаления от туда."""
        user = request.user
        if request.method == 'POST':
            recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))
            favorite, created = Favorites.objects.get_or_create(
                recipe=recipe, user=user
            )
            if not created:
                return Response(
                    {'detail': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = self.get_serializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, state = Favorites.objects.filter(
            recipe_id=kwargs.get('pk'), user=user
        ).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепта нет в избранном.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(['get'], detail=True, url_path='get-link')
    def get_link(self, request, *args, **kwargs):
        """Получение короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))
        short_link = recipe.short_link
        return Response(
            {
                'short-link': f'{ request.scheme }://'
                f'{ request.get_host() }/s/{short_link}/'
            },
            status=status.HTTP_200_OK,
        )


class DownloadView(viewsets.ViewSet):
    """Скачивание файла покупок.

    Позволяет зарегистрированным пользователям скачать список покупок.
    Список покупок скачивается одним файлов с суммированием ингредиентов
    из разных рецептов. Файл в формате CSV.
    """

    queryset = ShoppingCart.objects.all()
    serializer_class = DownloadShoppingCartSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return (
            self.queryset.filter(user=self.request.user)
            .values(
                'recipe__ingredients__ingredient__name',
                'recipe__ingredients__ingredient__measurement_unit',
            )
            .annotate(sum=Sum('recipe__ingredients__amount'))
        )

    @action(detail=False, methods=['get'], url_name='download_shopping_cart')
    def download(self, request):
        """Cкачиваниt файла списка покупок."""
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)

        csv_buffer = io.StringIO()
        csv_writer = csv.DictWriter(
            csv_buffer,
            fieldnames=SHOPPING_CART_FILE_HEADERS,
            extrasaction='ignore',
        )
        csv_writer.writeheader()

        for ingredient in serializer.data:
            csv_writer.writerow(ingredient)

        return HttpResponse(
            csv_buffer.getvalue(),
            headers={
                'Content-Disposition': 'attachment; filename="Shopping.csv"',
                'Accept': 'text/csv',
            },
            content_type='text/csv',
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def short_link_view(request, surl):
    """Функция перенаправления пользователей.

    При переходе по короткой ссылке рецепта
    пользователи перенаправляются на страцицу рецепта.
    """
    recipe = get_object_or_404(Recipe, short_link=surl)
    return redirect('recipes-detail', pk=recipe.id)
