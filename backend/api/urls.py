from django.urls import include, path
from rest_framework import routers

from api.views import (
    DownloadView, IngredientViewSet, TagViewSet,
    RecipeViewSet  # , AddDeleteRecipeShoppingCartViewSet, AddDeleteRecipeToFavoriteViewSet
)
router = routers.DefaultRouter()

router.register('recipes', RecipeViewSet)
# router.register(r'recipes/(?P<id>\d+)/shopping_cart', AddDeleteRecipeShoppingCartViewSet, basename='shopping_cart')
# router.register(r'recipes/(?P<id>\d+)/favorite', AddDeleteRecipeToFavoriteViewSet, basename='favorite')
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    # path('recipes/<int:id>/shopping_cart/',
    #      AddDeleteRecipeShoppingCartViewSet.as_view(
    #          {'post': 'create', 'delete': 'destroy'}
    #      ),
    #      name='shopping_cart'),
    # path('recipes/<int:id>/favorite/',
    #      AddDeleteRecipeToFavoriteViewSet.as_view(
    #          {'post': 'create', 'delete': 'destroy'}
    #      ),
    #      name='favorite'),
    path('recipes/download_shopping_cart/', DownloadView.as_view(
        {'get': 'download'})
    ),
    path('', include(router.urls)),
    path('', include('users.urls')),
]
