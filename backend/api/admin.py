from django.contrib import admin

from api.models import (
    Favorites, Ingredient, IngredientInRecipe, Recipe, RecipeTag, ShoppingCart, Tag
)


admin.site.empty_value_display = '-пусто-'


class FavoritesAdmin(admin.ModelAdmin):
    """Админка для избранного."""

    list_display = ('pk', 'recipe', 'user',)
    search_fields = ('user', 'recipe',)
    list_filter = ('user',)


class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""

    list_display = ('pk', 'name', 'measurement_unit',)
    search_fields = ('name',)


class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""

    list_display = ('pk', 'name', 'slug',)
    search_fields = ('name', 'slug',)


class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Админка для ингредиентов в рецептах."""

    list_display = ('pk', 'recipe', 'ingredient', 'amount',)
    search_fields = ('recipe', 'ingredient',)
    list_filter = ('recipe',)


class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    list_display = ('pk', 'name', 'author', 'cooking_time', 'text', 'image', 'short_link')
    search_fields = ('name', 'author',)
    list_filter = ('name', 'author',)


class RecipeTagAdmin(admin.ModelAdmin):
    """Админка для тегов рецептов."""

    list_display = ('pk', 'recipe', 'tag',)
    search_fields = ('recipe',)


class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для списка покупок."""

    list_display = ('pk', 'recipe', 'user',)
    search_fields = ('user', 'recipe',)
    list_filter = ('user',)

admin.site.register(Favorites, FavoritesAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(IngredientInRecipe, IngredientInRecipeAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeTag, RecipeTagAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
