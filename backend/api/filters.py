from django_filters.rest_framework import filters, FilterSet

from recipes.models import Recipe


class RecipeViewSetFilter(FilterSet):
    is_favorited = filters.BooleanFilter(
        field_name='is_favorited',
        method='is_favorited_filter'
    )
    author = filters.NumberFilter(
        field_name='author__id',
        lookup_expr='iexact',
    )
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='shopping_cart',
        method='is_in_shopping_cart_filter',
    )
    tags = filters.CharFilter(
        field_name='tags__slug',
        lookup_expr='iexact',
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
        )

    def is_favorited_filter(self, queryset, name, value):
        user = self.request.user
        if value is not None and user.is_authenticated:
            if value:
                return queryset.filter(favorite_recipe__user=user)
            else:
                return queryset.exclude(favorite_recipe__user=user)
        return queryset

    def is_in_shopping_cart_filter(self, queryset, name, value):
        if value is not None:
            if value:
                return queryset.filter(shopping_cart=True)
            else:
                return queryset.exclude(shopping_cart=True)
        return queryset
