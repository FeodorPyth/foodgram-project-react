from django.core.validators import MinValueValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (
    Favourite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscriptions,
    Tag
)
from users.models import User
from .services import (
    PHRASE_FOR_VALIDATE_FAVORITE,
    PHRASE_FOR_VALIDATE_SHOPPING_CART,
    add_tags_and_ingredients,
    validate_favorite_shopping_cart
)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели тегов на чтение данных."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов на чтение данных."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели связи рецептов и ингредиентов."""
    id = serializers.ReadOnlyField(
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class UserReadSerializer(UserSerializer):
    """Сериализатор для модели пользователей на чтение данных."""
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
    """Сериализатор для модели пользователей на запись данных."""

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'password',
            'username',
            'first_name',
            'last_name'
        )
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False, },
            'password': {'required': True, 'allow_blank': False, },
            'username': {'required': True, 'allow_blank': False, },
            'first_name': {'required': True, 'allow_blank': False, },
            'last_name': {'required': True, 'allow_blank': False, },
        }


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для поля ингредиентов для записи данных в модель Recipe."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message='Количество ингредиентов не может быть меньше 1.'
            ),
        )
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о рецептах."""
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
                'measurement_unit':
                recipe_ingredient.ingredient.measurement_unit,
                'amount': recipe_ingredient.amount,
            } for recipe_ingredient in obj.recipes.all()
        ]

    def get_is_favorited(self, obj):
        return Favourite.objects.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingCart.objects.filter(recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Serializer для модели Recipe - запись / обновление / удаление данных."""
    ingredients = RecipeIngredientCreateSerializer(
        many=True,
        write_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
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
            'author'
        )

    def validate(self, data):
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                'Необходимо указать ингредиенты!'
            )
        if 'tags' not in data:
            raise serializers.ValidationError(
                'Необходимо указать теги!'
            )
        if 'image' not in data or not data['image']:
            raise serializers.ValidationError(
                'Фотография рецепта обязательна!'
            )
        return super().validate(data)

    def validate_ingredients(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                "Добавьте хотя бы один ингредиент!"
            )
        for ingredient in value:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    "Количество ингредиента должно быть больше или равно 1."
                )
        ingredient_ids = [ingredient['id'] for ingredient in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться!'
            )
        return value

    def validate_tags(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                "Добавьте хотя бы один тег!"
            )
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                'Теги не должны повторяться!'
            )
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        add_tags_and_ingredients(ingredients, tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.ingredients.clear()
        add_tags_and_ingredients(ingredients, tags, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        representation = RecipeReadSerializer(instance).data
        return representation


class RecipeForSubscriptionsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для поля рецептов на чтение и запись данных в модель подписок.
    """
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
    """
    Сериализатор для чтения, создания и удаления данных для модели подписок.
    """
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

    def to_representation(self, instance):
        data = super(SubscriptionsSerializer, self).to_representation(instance)
        recipes = data.pop('recipes')
        recipes_limit = self.context.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        data['recipes'] = recipes
        return data

    def get_serializer_context(self, *args, **kwargs):
        context = super(SubscriptionsSerializer, self).get_serializer_context(
            *args, **kwargs
        )
        context['recipes_limit'] = self.context.get('recipes_limit')
        return context


class RecipeFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи и удаления данных для модели избранного."""
    id = serializers.PrimaryKeyRelatedField(
        source='recipe',
        read_only=True,
    )
    name = serializers.StringRelatedField(
        source='recipe.name',
        read_only=True,
    )
    image = Base64ImageField(
        source='recipe.image',
        read_only=True,
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True,
    )

    class Meta:
        model = Favourite
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )

    def validate(self, data):
        return validate_favorite_shopping_cart(
            self,
            data,
            Favourite,
            PHRASE_FOR_VALIDATE_FAVORITE
        )


class RecipeShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для записи и удаления данных для модели списка покупок."""
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

    def validate(self, data):
        return validate_favorite_shopping_cart(
            self,
            data,
            ShoppingCart,
            PHRASE_FOR_VALIDATE_SHOPPING_CART
        )
