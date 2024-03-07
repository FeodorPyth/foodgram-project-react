from django.contrib import admin
from django.template.defaulttags import format_html

from .models import (
    Favourite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscriptions,
    Tag,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Кастомный класс для регистрации модели ингредиентов в админке."""
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    """Модель рецептов и ингредиентов для вставки в модель рецептов."""
    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Кастомный класс для регистрации модели рецептов в админке."""
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'author', 'count_favourite_recipes', 'image_tag')
    list_filter = ('author__username', 'name', 'tags')
    search_fields = ('name',)
    filter_horizontal = ('tags',)
    readonly_fields = ['count_favourite_recipes',]

    def image_tag(self, obj):
        # return format_html('<img src="{}" width="35" />', obj.image.url)
        if obj.image:
            return format_html('<img src="{}" width="35" />', obj.image.url)
        return "No image"

    image_tag.short_description = 'Изображение рецепта'

    def count_favourite_recipes(self, obj):
        return obj.favorite_recipe.all().count()

    count_favourite_recipes.short_description = ('Общее число добавлений'
                                                 ' рецепта в избранное')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админ-зона для модели рецептов и ингредиентов."""
    list_display = ('recipe', 'ingredient',)
    list_filter = ('recipe', 'ingredient',)
    search_fields = ('recipe__name', 'ingredient__name')


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    """Кастомный класс для регистрации модели избранного в админке."""
    list_display = ('user', 'recipe',)
    list_filter = ('recipe',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(Subscriptions)
class SubscriptionsAdmin(admin.ModelAdmin):
    """Кастомный класс для регистрации модели подписок в админке."""
    list_display = ('follower', 'following',)
    list_filter = ('follower', 'following',)
    search_fields = ('follower__username', 'following__username')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Кастомный класс для регистрации модели тегов в админке."""
    list_display = ('name', 'color', 'slug')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Кастомный класс для регистрации модели списка покупок в админке."""
    list_display = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    search_fields = ('user__username', 'recipe__name')
