from django_filters.rest_framework import filters, FilterSet
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class RecipeViewSetFilter(FilterSet):
    """
    Кастомная модель фильтрации полей при выводе рецептов.
    -Фильтрация по полю автора проводится по его id.
    -Фильтрация по полю тегов проводится по его slug.
    -Фильтрация по полю избранного проводится по наличию флага присутствия.
    -Фильтрация по полю списка покупок проводится по наличию флага присутствия.
    """
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited')
    author = filters.NumberFilter(
        field_name='author__id',
        lookup_expr='iexact',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorite_recipe__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset


class IngredientViewSetFilter(SearchFilter):
    """Кастомная модель фильтрации полей при выводе ингредиентов."""
    search_param = 'name'
