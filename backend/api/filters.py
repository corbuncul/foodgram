from api.models import Ingredient, Recipe, Tag
from django_filters import rest_framework as filters


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith',)

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(
        field_name='author__id', lookup_expr='exact')
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
        conjoined=False)

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if value:
            return queryset.filter(is_favorited__user=user)
        return queryset.exclude(is_favorited__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if value:
            return queryset.filter(is_in_shopping_cart__user=user)
        return queryset.exclude(is_in_shopping_cart__user=user)
