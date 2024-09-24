from api import constants
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        max_length=constants.TAG_NAME_MAX_LENGTH,
        verbose_name='Название тега',
    )
    slug = models.SlugField(
        unique=True,
        validators=[
            RegexValidator(
                regex=constants.TAG_SLUG_CHECK,
                message=(
                    'Слаг может содержать только буквы и цыфры и '
                    f'{constants.TAG_SLUG_CHECK} символы.'
                ),
            ),
        ],
        error_messages={
            'unique': 'Тег с таким слагом уже есть.',
        },
        verbose_name='Идентификатор',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}'


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        max_length=constants.INGREDIENT_NAME_MAX_LENGTH,
        unique=True,
        error_messages={
            'unnique': 'Такой ингредиент уже есть.',
        },
        verbose_name='Ингредиент',
    )
    measurement_unit = models.CharField(
        max_length=constants.INGREDIENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}'


class Recipe(models.Model):
    """Модель рецептов."""

    name = models.CharField(
        max_length=constants.RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название рецепта',
    )
    text = models.TextField(
        verbose_name='Описание рецепта'
    )
    image = models.ImageField(
        upload_to='recipe/images/',
        blank=True,
        default=None,
        verbose_name='Изображение рецепта'
    )
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag, through='RecipeTag',
        verbose_name='Теги'
    )
    cooking_time = models.SmallIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(constants.MIN_COOK_TIME)
        ],
        error_messages={
            'validators': 'Время приготовления не может'
            f'быть меньше {constants.MIN_COOK_TIME}'
        }
    )
    short_link = models.CharField(
        'короткая ссылка', db_index=True,
        max_length=constants.LINK_MAX_LENGTH,
        unique=True,
    )
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('pub_date',)

    def __str__(self):
        return f'{self.name}'


class IngredientInRecipe(models.Model):
    """Модель, ингредиентов в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='+'
    )
    amount = models.SmallIntegerField(
        'Количество ингредиента',
        validators=[
            MinValueValidator(constants.MIN_AMOUNT)
        ]
    )

    class Meta:
        verbose_name = 'Игредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return f'{self.recipe.name} {self.ingredient.name} {self.amount}'


class RecipeTag(models.Model):
    """Модель тегов у рецептов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete= models.CASCADE,
        verbose_name='Тег',
        related_name='tags'
    )

    class Meta:
        verbose_name = 'Теги рецепта'
        verbose_name_plural = 'Теги рецептов'

    def __str__(self):
        return f'{self.recipe.name} {self.tag.name}'


class UserRecipeModel(models.Model):
    """Базовая модель для списка покупок и избранного."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.user.username} {self.recipe.name}'


class ShoppingCart(UserRecipeModel):
    """Модель списка покупок."""

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'is_in_shopping_cart'


class Favorites(UserRecipeModel):
    """Модель избранного."""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'is_favorited'
