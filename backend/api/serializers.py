from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.core.validators import MinValueValidator

from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    RecipeIngredient,
    Favourite,
    ShoppingCart,
    Subscriptions,
)
from users.models import User


class TagSerializer(serializers.ModelSerializer):
    """
    """
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    """
    """
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.StringRelatedField(
        source='ingredient.name'
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit'
    )
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'amount',
            'name',
            'measurement_unit',
            'id'
        )


class UserReadSerializer(UserSerializer):
    """
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        try:
            return obj.following_subscriptions.exists()
        except AttributeError:
            return False


class CustomUserCreateSerializer(UserCreateSerializer):
    """
    """

    class Meta:
        model = User
        fields = ("email",
                  "id",
                  "password",
                  "username",
                  "first_name",
                  "last_name")
        extra_kwargs = {
            "email": {"required": True, 'allow_blank': False, },
            "password": {"required": True, 'allow_blank': False, },
            "username": {"required": True, 'allow_blank': False, },
            "first_name": {"required": True, 'allow_blank': False, },
            "last_name": {"required": True, 'allow_blank': False, },
        }


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = UserReadSerializer(read_only=True, many=False)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

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

    def get_ingredients(self, obj):
        return [
            {
                'id': recipe_ingredient.ingredient.id,
                'name': recipe_ingredient.ingredient.name,
                'measurement_unit': recipe_ingredient.ingredient.measurement_unit,
                'amount': recipe_ingredient.quantity,
            } for recipe_ingredient in obj.recipeingredient_set.all()
        ]

    def get_is_favorited(self, obj):
        return Favourite.objects.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingCart.objects.filter(recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = RecipeIngredientCreateSerializer(many=True)
    # FIX: на вермя отладки закомментил,
    # чтобы с файлами в тестах не морочиться.
    # image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message="Время приготовления не может быть меньше 1!"
            ),
        )
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )
        # FIX: Лучше напрямую в полях указать. А если в модели обязательное,
        # то drf в сериалайзере тоже сделает поле обязательным.
        # extra_kwargs = {
        #     "ingredients": {"required": True, 'allow_blank': False, },
        #     "tags": {"required": True, 'allow_blank': False, },
        #     "image": {"required": True, 'allow_blank': False, },
        #     "name": {"required": True, 'allow_blank': False, },
        #     "text": {"required": True, 'allow_blank': False, },
        #     "cooking_time": {"required": True, 'allow_blank': False, },
        # }

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )
        recipe.tags.set(tags)
        return recipe

    # FIX: Здесь и была заковыка.
    # Твой код, ничего не менял, просто раскомментировал.
    def to_representation(self, obj):
        """Возвращаем прдеставление в таком же виде, как и GET-запрос."""
        self.fields.pop('ingredients')
        representation = super().to_representation(obj)
        representation['ingredients'] = RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=obj).all(), many=True
        ).data
        return representation

    # def update(self, instance, validated_data):
    #     ingredients = validated_data.pop('ingredients', None)
    #     tags = validated_data.pop('tags', None)
    #     if tags is not None:
    #         instance.tags.clear()
    #         instance.tags.set(tags)
    #     if ingredients is not None:
    #         instance.ingredients.clear()

    #         create_ingredients = [
    #             RecipeIngredient(
    #                 recipe=instance,
    #                 ingredient=ingredient['ingredient'],
    #                 amount=ingredient['amount']
    #             )
    #             for ingredient in ingredients
    #         ]
    #         RecipeIngredient.objects.bulk_create(
    #             create_ingredients
    #         )
    #     return super().update(instance, validated_data)


class RecipeForSubscriptionsSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class SubscriptionsSerializer(serializers.ModelSerializer):
    """"""
    email = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeForSubscriptionsSerializer(many=True, read_only=True)
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
        )

    def validate(self, data):
        request = self.context.get('request')
        following_user = self.instance
        if following_user == request.user:
            raise ValidationError("Нельзя подписаться на самого себя!")
        if Subscriptions.objects.filter(
            follower=request.user,
            following=following_user
        ).exists():
            raise ValidationError("Вы уже подписаны на этого пользователя!")

        return data

    def get_is_subscribed(self, obj):
        try:
            return obj.following_subscriptions.exists()
        except AttributeError:
            return False

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='recipe',
        read_only=True
    )
    name = serializers.StringRelatedField(
        source='recipe.name',
        read_only=True
    )
    image = Base64ImageField(
        source='recipe.image',
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True
    )

    class Meta:
        model = Favourite
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class RecipeShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='recipe',
        read_only=True
    )
    name = serializers.StringRelatedField(
        source='recipe.name',
        read_only=True
    )
    image = Base64ImageField(
        source='recipe.image',
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True
    )

    class Meta:
        model = ShoppingCart
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )