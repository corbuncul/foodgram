import csv
import io

from api.constants import SHOPPING_CART_FILE_HEADERS
from api.filters import IngredientFilter, RecipeFilter
from api.models import Favorites, Ingredient, Recipe, ShoppingCart, Tag
from api.permissions import IsAuthorOrReadOnly, ReadOnly
from api.serializers import (DownloadShoppingCartSerializer,
                             FavoriteSerializer, IngredientSerializer,
                             RecipeReadSerializer, RecipeWriteSerializer,
                             ShoppingCartSerializer, TagSerializer)
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Представление ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        return super().perform_create(serializer)

    def get_serializer_class(self):
        if self.action == 'shopping_cart':
            return ShoppingCartSerializer
        if self.action == 'favorite':
            return FavoriteSerializer
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_permissions(self):
        if self.action in ('list', 'get_link'):
            return [ReadOnly(),]
        if self.action in ('create', 'shopping_cart', 'favorite'):
            return [IsAuthenticated(),]
        return [IsAuthorOrReadOnly(),]

    @action(
        ['post', 'delete'],
        detail=True,
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, *args, **kwargs):
        """Экшн для добавления рецепта в список покупок и удаления от туда."""
        user = request.user
        id = kwargs.get('pk')
        recipe = get_object_or_404(Recipe, id=id)
        if request.method == 'POST':
            request.data['id'] = id
            serializer = self.get_serializer(
                data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        obj = ShoppingCart.objects.filter(recipe=recipe, user=user)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепта нет в списке покупок.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        ['post', 'delete'],
        detail=True,
        url_path='favorite',
    )
    def favorite(self, request, *args, **kwargs):
        """Экшн для добавления рецепта в избранное и удаления от туда."""
        user = request.user
        id = kwargs.get('pk')
        recipe = get_object_or_404(Recipe, id=id)
        if request.method == 'POST':
            request.data['id'] = id
            serializer = self.get_serializer(
                data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        obj = Favorites.objects.filter(recipe=recipe, user=user)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепта нет в избранном.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        ['get',], detail=True, url_path='get-link'
    )
    def get_link(self, request, *args, **kwargs):
        """Экшн для получения короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))
        short_link = recipe.short_link
        return Response(
            {'short-link': f'{ request.scheme }://'
             f'{ request.get_host() }/s/{short_link}/'},
            status=status.HTTP_200_OK
        )


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


@api_view(['GET',])
@permission_classes([AllowAny,])
def short_link_view(request, surl):
    """
    Функция перенаправления пользователей
    при переходе по короткой ссылке рецепта на страцицу рецепта.
    """
    recipe = get_object_or_404(Recipe, short_link=surl)
    return redirect('recipe-detail', pk=recipe.id)
