import base64
import os

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from recipes import constants
from recipes.models import (Favorites, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from recipes.utils import generate_random_str
from users.models import Follow

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле для загрузки изображений в формате base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserSerializer(BaseUserSerializer):
    """Сериализатор для пользователей."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, following):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Follow.objects.filter(user=user, following=following).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления автара"""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    name = serializers.CharField(read_only=True, required=False)
    slug = serializers.SlugField(read_only=True, required=False)

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    measurement_unit = serializers.CharField(read_only=True, required=False)
    name = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class AmountSerializer(serializers.ModelSerializer):
    """Сериализатор для количества ингредиентов."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name', required=False)
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit', required=False
    )
    amount = serializers.IntegerField(required=True)

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class AmountShortSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='ingredient')

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'amount',
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = AmountSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.favorited.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.in_shopping_cart.filter(user=user).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), required=True, many=True
    )
    ingredients = AmountShortSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate(self, attrs):
        errors = []
        if 'ingredients' not in attrs:
            errors.append('Отсутствует список ингредиентов.')
        if 'ingredients' in attrs and len(attrs.get('ingredients')) == 0:
            errors.append('Список ингредиентов пуст.')
        if 'tags' not in attrs:
            errors.append('Отсутствует список тегов.')
        if 'tags' in attrs and len(attrs.get('tags')) == 0:
            errors.append('Список тегов пуст.')
        if 'ingredients' in attrs:
            ingredients = attrs.get('ingredients')
            ingredient_set = {ingredient['ingredient'] for ingredient in ingredients}
            if len(ingredients) != len(ingredient_set):
                errors.append('Ингредиенты повторяются.')
            for ingredient in ingredient_set:
                if not Ingredient.objects.filter(id=ingredient).exists():
                    errors.append(f'Ингредиента {ingredient} не существует.')
        if 'tags' in attrs:
            tags = attrs.get('tags')
            if len(tags) != len(set(tags)):
                errors.append('Теги повторяются.')
        if errors:
            raise serializers.ValidationError({'errors': errors})
        return super().validate(attrs)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context['request'].user
        validated_data['author'] = author
        validated_data['short_link'] = generate_random_str(
            constants.LENGTH_SHORT_LINK
        )
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingr_obj = get_object_or_404(
                Ingredient, id=ingredient['ingredient']
            )
            ingr_in_recipe, st = IngredientInRecipe.objects.get_or_create(
                ingredient=ingr_obj, recipe=recipe, amount=amount
            )
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredients.all().delete()
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingr_obj = get_object_or_404(
                Ingredient, id=ingredient['ingredient']
            )
            ingr_in_recipe, st = IngredientInRecipe.objects.update_or_create(
                ingredient=ingr_obj, recipe=instance, amount=amount
            )
            ingr_in_recipe.save()
        instance.tags.clear()
        instance.tags.set(tags)
        return super().update(instance=instance, validated_data=validated_data)

    def to_representation(self, instance):
        request = self.context['request']
        return RecipeReadSerializer(
            instance, context={'request': request}
        ).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов с полями id, name, image, cooking_time."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели списка покупок."""

    recipe = RecipeShortSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('recipe',)

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели избранного."""

    recipe = RecipeShortSerializer(read_only=True)

    class Meta:
        model = Favorites
        fields = ('recipe',)

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe).data


class DownloadShoppingCartSerializer(serializers.Serializer):
    """Сериализатор для скачивания списка покупок."""

    ingredient = serializers.CharField(
        source='recipe__ingredients__ingredient__name'
    )
    amount = serializers.IntegerField(source='sum')
    unit = serializers.CharField(
        source='recipe__ingredients__ingredient__measurement_unit'
    )

    class Meta:
        fields = (
            'ingredient',
            'amount',
            'unit',
        )
        read_only_fields = (
            'ingredient',
            'amount',
            'unit',
        )


class FollowSerializer(serializers.ModelSerializer):
    """Сериалайзер для подписок."""

    id = serializers.IntegerField(source='following.id')

    class Meta:
        model = Follow
        fields = ('id',)

    def create(self, validated_data):
        following = validated_data['following']
        user = validated_data['user']
        Follow.objects.create(following=following, user=user)
        return following

    def to_representation(self, instance):
        request = self.context['request']
        return UserRecipeSerializer(
            instance, context={'request': request}
        ).data


class UserRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для отображения пользователей и их рецептов."""

    recipes = serializers.SerializerMethodField('paginated_recipe')
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )
        read_only_fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, following):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Follow.objects.filter(user=user, following=following).exists()
        )

    def get_recipes_count(self, instance):
        return instance.recipes.count()

    def paginated_recipe(self, obj):
        page_size = (
            self.context['request'].query_params.get('recipes_limit')
            or constants.NUMBER_OF_RECIPES
        )
        paginator = Paginator(obj.recipes.all(), page_size)
        page = 1

        users_recipe = paginator.page(page)
        serializer = RecipeShortSerializer(users_recipe, many=True)

        return serializer.data
