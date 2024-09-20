import base64

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from api import constants
from api.models import (
    Favorites, Ingredient, IngredientInRecipe,
    Recipe, RecipeTag, ShoppingCart, Tag
)
from api.utils import generate_random_str
from users.models import Follow
from users.serializers import UserSerializer


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле для загрузки изображений в формате base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    name = serializers.CharField(read_only=True, required=False)
    slug = serializers.SlugField(read_only=True, required=False)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    measurement_unit = serializers.CharField(read_only=True, required=False)
    name = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class AmountSerializer(serializers.ModelSerializer):
    """Сериализатор для количества ингредиентов."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name', required=False)
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
        required=False
    )
    amount = serializers.IntegerField(required=True)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class AmountShortSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='ingredient')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount',)


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
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.is_favorited.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and obj.is_in_shopping_cart.filter(user=user).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        required=True,
        many=True
    )
    ingredients = AmountShortSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )

    def validate(self, attrs):
        errors = []
        if 'ingredients' not in attrs:
            errors.append('Отсутствует список ингредиентов.')
        if 'ingredients' in attrs and len(attrs.get('ingredients')) == 0:
            errors.append('Список ингредиентов пуст.')
        if 'tags' not in attrs or len(attrs.get('tags')) == 0:
            errors.append('Отсутствует список тегов.')
        if 'tags' in attrs and len(attrs.get('tags')) == 0:
            errors.append('Список тегов пуст.')
        if 'ingredients' in attrs:
            ingredients = attrs.get('ingredients')
            ingredient_set = {i['ingredient'] for i in ingredients}
            if len(ingredients) != len(ingredient_set):
                errors.append('Ингредиенты повторяются.')
        if 'tags' in attrs:
            tags = attrs.get('tags')
            if len(tags) != len(set(tags)):
                errors.append('Теги повторяются.')
        if errors:
            raise serializers.ValidationError(errors)
        return super().validate(attrs)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context['request'].user
        validated_data['author'] = author
        validated_data['short_link'] = generate_random_str(
            constants.LENGTH_SHOT_LINK
        )
        recipe = Recipe.objects.create(**validated_data) # anonim роняет
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
        ingredients = validated_data.pop('ingredients') # keyerror
        tags = validated_data.pop('tags') # keyerror
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        image = validated_data.get('image', instance.image)
        if image:
            instance.image = image
        instance.save()
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
        return instance

    def to_representation(self, instance):
        request = self.context['request']
        return RecipeReadSerializer(
            instance, context={'request': request}
        ).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов с полями id, name, image, cooking_time."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели списка покупок."""

    recipe = RecipeShortSerializer(read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('recipe',)

    def create(self, validated_data):
        recipe = get_object_or_404(Recipe, id=validated_data['id'])
        obj, st = self.model.objects.get_or_create(
            user=validated_data['user'], recipe=recipe
        )
        return obj

    def validate(self, attrs):
        recipe = get_object_or_404(Recipe, id=attrs['id']) # keyerror
        if self.model.objects.filter(
            user=self.context['reqiest'].user, recipe=recipe
        ).exists():
            raise serializers.ValidationError('Объект уже существует.')
        return super().validate(attrs)


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели избранного."""

    recipe = RecipeShortSerializer(read_only=True)

    class Meta:
        model = Favorites
        fields = ('recipe',)

    def create(self, validated_data):
        recipe = get_object_or_404(Recipe, id=validated_data['id'])
        obj, st = self.model.objects.get_or_create(
            user=validated_data['user'], recipe=recipe
        )
        return obj

    def validate(self, attrs):
        recipe = get_object_or_404(Recipe, id=attrs['id']) # keyerror
        if self.model.objects.filter(
            user=self.context['reqiest'].user, recipe=recipe
        ).exists():
            raise serializers.ValidationError('Объект уже существует.')
        return super().validate(attrs)


class DownloadShoppingCartSerializer(serializers.Serializer):
    """Сериализатор для скачивания списка покупок."""

    ingredient = serializers.CharField(source='recipe__ingredients__ingredient__name')
    amount = serializers.IntegerField(source='sum')
    unit = serializers.CharField(source='recipe__ingredients__ingredient__measurement_unit')

    class Meta:
        fields = ('ingredient', 'amount', 'unit',)
        read_only_fields = ('ingredient', 'amount', 'unit',)


class FollowSerializer(serializers.ModelSerializer):
    """Сериалайзер для подписок."""

    id = serializers.IntegerField(source='following.id')

    class Meta:
        model = Follow
        fields = ('id',)

    def validate(self, data):
        user = self.context['request'].user
        id = data['following']['id']
        following = get_object_or_404(User, id=id)
        follow = Follow.objects.filter(user=user, following=following)
        if self.context['request'].method == 'DELETE' and not follow.exists():
            raise serializers.ValidationError('Подписки не существует.')
        if user == following:
            raise serializers.ValidationError(
                'Подписка на самого себя запрещена.'
            )
        if follow.exists():
            raise serializers.ValidationError(
                'Подписка уже существует.'
            )
        data['user'] = user
        return super().validate(data)

    def create(self, validated_data):
        following = User.objects.get(id=validated_data['following']['id'])
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

    recipes = RecipeShortSerializer(many=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )
        read_only_fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_is_subscribed(self, following):
        user = self.context['request'].user
        return (
            user.is_authenticated
            and Follow.objects.filter(user=user, following=following).exists()
        )

    def get_recipes_count(self, instance):
        return instance.recipes.count()
