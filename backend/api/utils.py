import string
import random

from api.models import Recipe


def generate_random_str(num=8):
    """Генерирование короткой ссылки."""
    while True:
        short_link = ''.join(random.SystemRandom().choice(
            string.ascii_uppercase
            + string.ascii_lowercase
            + string.digits
        ) for _ in range(num))
        if not Recipe.objects.filter(short_link=short_link).exists():
            break
    return short_link

# view
# from django.http import (HttpResponseRedirect, Http404)

# from .models import ShortLink


# def map_link(request, **kwargs):
#     path = kwargs.get('path', '')
#     s = ShortLink.objects.filter(short_path=path).first()
#     if s:
#         return HttpResponseRedirect(s.full_url)
#     raise Http404

# url
# from django.urls import re_path

# from .views import map_link
# from .settings import SHORTLINK_URL_BASE


# urlpatterns = [
#     re_path('^{}(?P<path>[a-zA-Z0-9 _-]+)$'.format(SHORTLINK_URL_BASE), map_link, name='map_link'),
# ]

# model кусок
# @property
#     def short_url(self):
#         """ Complete short url
#         Pattern:
#             short_url = HOST_ADDRESS + '/' +  SHORTLINK_URL_BASE + shorten_path
#         """
#         return '{}/{}{}'.format(
#             HOST_ADDRESS,
#             SHORTLINK_URL_BASE,
#             self.short_path
#         )

#     def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
#         if not self.short_path:
#             self.generate_short_path(commit=False)
#             # Don't save cause will call save() later.

#         if not self.name:
#             self.name = self.full_url
#         super(ShortLink, self).save()

#     def generate_short_path(self, commit=True):
#         # Loop until a not used path found!
#         while True:
#             path = generate_random_str(SHORTEN_PATH_LENGTH)
#             if not ShortLink.objects.filter(short_path=path).exists():
#                 break
#         self.short_path = path
#         if commit:
#             self.save()
