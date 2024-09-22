from django.urls import include, path
from rest_framework import routers

from api.views import (
    DownloadView, IngredientViewSet, TagViewSet,
    RecipeViewSet
)
router = routers.DefaultRouter()

router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('recipes/download_shopping_cart/', DownloadView.as_view(
        {'get': 'download'})
    ),
    path('', include(router.urls)),
    path('', include('users.urls')),
]
