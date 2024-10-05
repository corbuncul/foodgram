from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest

from recipes.models import (
    Favorites,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    RecipeTag,
    ShoppingCart,
    Tag,
)

admin.site.empty_value_display = '-пусто-'


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    """Админка для избранного."""

    list_display = (
        'pk',
        'recipe',
        'user',
    )
    list_display_links = (
        'recipe',
        'user',
    )
    search_fields = (
        'user__username',
        'recipe__name',
    )
    list_filter = (
        'recipe',
        'user',
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        return qs.select_related('user', 'recipe')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""

    list_display = (
        'name',
        'measurement_unit',
    )
    search_fields = ('name',)
    list_display_links = ('name',)


class IngredientInline(admin.StackedInline):
    model = IngredientInRecipe
    extra = 0


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""

    list_display = (
        'pk',
        'name',
        'slug',
    )
    search_fields = (
        'name',
        'slug',
    )
    list_display_links = ('name',)


class TagInline(admin.StackedInline):
    model = RecipeTag
    extra = 0


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Админка для ингредиентов в рецептах."""

    list_display = (
        'pk',
        'recipe',
        'ingredient',
        'amount',
    )
    list_display_links = (
        'ingredient',
        'recipe',
    )
    search_fields = (
        'recipe__name',
        'ingredient__name',
    )
    list_filter = (
        'recipe',
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        return qs.select_related('ingredient', 'recipe')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    inlines = [IngredientInline, TagInline]
    list_display = ('name', 'author', 'favorited_count')
    search_fields = (
        'name',
        'author__username',
    )
    list_filter = (
        'author',
        'tags',
    )
    list_display_links = ('name',)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        return qs.select_related('author').prefetch_related('tags', 'ingredients__ingredient')

    @admin.display(description='В избранном')
    def favorited_count(self, recipe: Recipe):
        return Favorites.objects.filter(recipe=recipe).count()


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    """Админка для тегов рецептов."""

    list_display = (
        'pk',
        'recipe',
        'tag',
    )
    list_display_links = (
        'recipe',
        'tag',
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для списка покупок."""

    list_display = (
        'pk',
        'recipe',
        'user',
    )
    list_display_links = (
        'recipe',
        'user',
    )
    search_fields = (
        'user__username',
        'recipe__name',
    )
    list_filter = (
        'user',
        'recipe',
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        qs = super().get_queryset(request)
        return qs.select_related('user', 'recipe')
