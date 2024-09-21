from django_filters.rest_framework import CharFilter, FilterSet

from api.models import Ingredient


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='istartswith',)

    class Meta:
        model = Ingredient
        fields = ('name',)
