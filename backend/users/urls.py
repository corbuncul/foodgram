from django.urls import include, path
from rest_framework import routers
from users.views import UserViewSet

router = routers.DefaultRouter()

router.register('', UserViewSet, basename='users')
urlpatterns = [
    path('users/', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken'))
]
