from django.contrib import admin
from django.template.defaulttags import format_html

from .models import (
    Tag,
    Favourite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscriptions,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'author', 'count_favourite_recipes', 'image_tag')
    list_filter = ('author__username', 'name', 'tags')
    search_fields = ('name',)
    filter_horizontal = ('tags',)
    readonly_fields = ['count_favourite_recipes',]

    def image_tag(self, obj):
        return format_html('<img src="{}" width="35" />', obj.image.url)

    image_tag.short_description = 'Изображение рецепта'

    def count_favourite_recipes(self, obj):
        return obj.favourites.all().count()

    count_favourite_recipes.short_description = ('Общее число добавлений'
                                                 ' рецепта в избранное')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient',)
    list_filter = ('recipe', 'ingredient',)
    search_fields = ('recipe__name', 'ingredient__name')


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    list_filter = ('recipe',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(Subscriptions)
class SubscriptionsAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following',)
    list_filter = ('follower', 'following',)
    search_fields = ('follower__username', 'following__username')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    search_fields = ('user__username', 'recipe__name')
