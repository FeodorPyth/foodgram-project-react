from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from foodgram.settings import AUTH_USER_MODEL

BLACK = '#000000'
SILVER = '#C0C0C0'
GRAY = '#808080'
WHITE = '#FFFFFF'
MAROON = '#800000'
RED = '#FF0000'
PURPLE = '#800080'
FUCHSIA = '#FF00FF'
GREEN = '#008000'
LIME = '#00FF00'
OLIVE = '#808000'
YELLOW = '#FFFF00'
NAVY = '#000080'
BLUE = '#0000FF'
TEAL = '#008080'
AQUA = '#00FFFF'


CHOICES_COLOR = (
    (BLACK, 'черный'),
    (SILVER, 'серебристый'),
    (GRAY, 'серый'),
    (WHITE, 'белый'),
    (MAROON, 'бордовый'),
    (RED, 'красный'),
    (PURPLE, 'фиолетовый'),
    (FUCHSIA, 'фуксия'),
    (GREEN, 'зеленый'),
    (LIME, 'лаймовый'),
    (OLIVE, 'оливковый'),
    (YELLOW, 'желтый'),
    (NAVY, 'темно-синий'),
    (BLUE, 'синий'),
    (TEAL, 'бирюзовый'),
    (AQUA, 'аквамарин'),
)


class Recipe(models.Model):
    """Модель рецептов."""
    name = models.CharField(
        max_length=200,
        blank=False,
        null=False,
        verbose_name='Название рецепта',
    )
    text = models.TextField(
        max_length=1024,
        blank=False,
        null=False,
        verbose_name='Описание рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        blank=False,
        null=False,
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
        blank=False,
        null=False,
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
        blank=False,
        null=False,
        verbose_name='Автор рецепта',
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=False,
        verbose_name='Тег рецепта',
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        blank=False,
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
    """Модель тегов."""
    name = models.CharField(
        max_length=50,
        unique=True,
        blank=False,
        null=False,
        verbose_name='Название тега',
    )
    color = models.CharField(
        max_length=len(max(
            [value for name, value in dict(CHOICES_COLOR).items()], key=len
        )),
        unique=True,
        blank=False,
        null=False,
        choices=CHOICES_COLOR,
        default=WHITE,
        help_text='Выберите цвет тега.',
        verbose_name='Цветовой код тега',
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        blank=False,
        null=False,
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
        max_length=50,
        blank=False,
        null=False,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=10,
        blank=False,
        null=False,
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
    """Модель связи рецепта и ингредиентов (многие ко многим)."""
    amount = models.PositiveSmallIntegerField(
        blank=False,
        null=False,
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

    def __str__(self):
        return f'{self.ingredient} в {self.recipe}.'


class Favourite(models.Model):
    """Модель избранных рецептов."""
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Объект избранного'
        verbose_name_plural = 'Объекты избранного'
        default_related_name = 'favourites'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_user_recipe'
            )
        ]

    def __str__(self):
        return f'{self.recipe} в избранном у пользователя {self.user}.'


class ShoppingCart(models.Model):
    "Модель списка покупок."
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart'
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
