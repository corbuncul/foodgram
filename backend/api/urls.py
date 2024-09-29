from django.urls import include, path
from rest_framework import routers

from api.views import (DownloadView, IngredientViewSet, RecipeViewSet,
                       TagViewSet, UserViewSet)

router = routers.DefaultRouter()

router.register('users', UserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path(
        'recipes/download_shopping_cart/',
        DownloadView.as_view({'get': 'download'}),
    ),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
