import random
import string

from recipes.constants import LENGTH_SHORT_LINK
from recipes.models import Recipe


def generate_random_str(num: int = LENGTH_SHORT_LINK) -> str:
    """Генерирование короткой ссылки."""
    while True:
        short_link = ''.join(
            random.choice(
                string.ascii_uppercase + string.ascii_lowercase + string.digits
            )
            for _ in range(num)
        )
        if not Recipe.objects.filter(short_link=short_link).exists():
            break
    return short_link
