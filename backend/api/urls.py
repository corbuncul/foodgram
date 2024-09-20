from django.urls import include, path
from rest_framework import routers

from api.views import (
    DownloadView, IngredientViewSet, TagViewSet,
    RecipeViewSet, AddDeleteRecipeShoppingCartViewSet,
    AddDeleteRecipeToFavoriteViewSet
)
router = routers.DefaultRouter()

router.register('recipes', RecipeViewSet)
router.register(r'recipes/(?P<id>\d+)/shopping_cart', AddDeleteRecipeShoppingCartViewSet, basename='shopping_cart')
router.register(r'recipes/(?P<id>\d+)/favorite', AddDeleteRecipeToFavoriteViewSet, basename='favorite')
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    # path(r'recipes/(?P<id>\d+$)/shopping_cart/',
    #      AddDeleteRecipeShoppingCartViewSet.as_view(
    #          {'post': 'create', 'delete': 'destroy'}
    #      ),
    #      name='shopping_cart'),
    # path(r'recipes/<int:id>/favorite/',
    #      AddDeleteRecipeToFavoriteViewSet.as_view(
    #          {'post': 'create', 'delete': 'destroy'}
    #      ),
    #      name='favorite'),
    path('recipes/download_shopping_cart/', DownloadView.as_view(
        {'get': 'download'})
    ),
    # path(r'users/<int:id>/subscribe/', SubscribeViewSet.as_view(
    #     {'post': 'subscribe', 'delete': 'subscribe'}
    # ), name='subscribe'),
    # path(r'users/subscriptions/', SubscribeViewSet.as_view(
    #     {'get': 'subscriptions'}
    # ), name='subscriptions'),
    # path(r'users/me/avatar/', AvatarUpdateDeleteViewSet.as_view(
    #     {'put': 'update', 'delete': 'destroy'}), name='avatar'
    # ),
    path('', include(router.urls)),
    path('', include('users.urls')),
]
