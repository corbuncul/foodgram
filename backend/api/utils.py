import random
import string

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
