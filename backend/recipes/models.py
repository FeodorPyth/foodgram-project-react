from colorfield.fields import ColorField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from foodgram.constants import (
    CHOICES_COLOR,
    DEFAULT_COLOR,
    LENGTH_FOR_MEASUREMENT_UNIT,
    LENGTH_FOR_NAME,
    LENGTH_FOR_TAG_NAME_SLUG,
    LENGTH_FOR_TEXT
)
from foodgram.settings import AUTH_USER_MODEL


class BaseModel(models.Model):
    """Базовая модель для моделей избранного и списка покупок."""
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)s_user',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='%(class)s_recipe',
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True


class Recipe(models.Model):
    """Модель рецептов."""
    name = models.CharField(
        max_length=LENGTH_FOR_NAME,
        verbose_name='Название рецепта',
    )
    text = models.TextField(
        max_length=LENGTH_FOR_TEXT,
        verbose_name='Описание рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                1,
                message='Время приготовления блюда должно'
                        ' начинаться от 1 минуты.'
            ),
        ],
        verbose_name='Время приготовления рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/',
        default=None,
        verbose_name='Картинка',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации рецепта',
        db_index=True,
    )
    author = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Тег рецепта',
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты',
    )

    class Meta:
        ordering = ('-pub_date', 'name', 'author',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'author'),
                name='unique_recipe_name_author'
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    Модель тегов.
    Реализован предустановленный выбор цветов в формате hex.
    """
    name = models.CharField(
        max_length=LENGTH_FOR_TAG_NAME_SLUG,
        unique=True,
        verbose_name='Название тега',
    )
    color = ColorField(
        max_length=len(max(
            [value for name, value in dict(CHOICES_COLOR).items()], key=len
        )),
        unique=True,
        choices=CHOICES_COLOR,
        default=DEFAULT_COLOR,
        help_text='Выберите цвет тега.',
        verbose_name='Цветовой код тега',
    )
    slug = models.SlugField(
        max_length=LENGTH_FOR_TAG_NAME_SLUG,
        unique=True,
        verbose_name='Слаг тега',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""
    name = models.CharField(
        max_length=LENGTH_FOR_NAME,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=LENGTH_FOR_MEASUREMENT_UNIT,
        verbose_name='Единицы измерения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_name_measurement_unit'
            )
        ]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связи рецептов и ингредиентов (многие ко многим)."""
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                1,
                message='Количество ингредиентов должно быть больше одного'
            ),
        ],
        verbose_name='Количество ингредиентов',
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredients_recipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} в {self.recipe}.'


class Favorite(BaseModel):
    """Модель избранных рецептов."""
    class Meta:
        verbose_name = 'Объект избранного'
        verbose_name_plural = 'Объекты избранного'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.recipe} в избранном у пользователя {self.user}.'


class ShoppingCart(BaseModel):
    "Модель списка покупок."
    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe'
            ),
        ]

    def __str__(self):
        return f'{self.recipe} в списке покупок у пользователя {self.user}.'


class Subscriptions(models.Model):
    "Модель подписок."
    follower = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follower_subscriptions',
        verbose_name='Пользователь, который подписывается на других',
    )
    following = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following_subscriptions',
        verbose_name='Пользователь, на которого подписаны',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('follower', 'following'),
                name='unique_follower_following'
            ),
        ]

    def __str__(self):
        return f'{self.follower} подписан на пользователя {self.following}.'

    def clean(self):
        if self.follower == self.following:
            raise ValidationError('Нельзя подписаться на самого себя!')
