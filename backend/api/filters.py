from django_filters import rest_framework

from recipes.models import Recipe


class RecipeViewSetFilter(rest_framework.FilterSet):
    is_favorited = rest_framework.BooleanFilter(
        method='filter_is_favorited',
    )
    author = rest_framework.NumberFilter(
        field_name='author__id',
        lookup_expr='iexact',
    )
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='filter_is_in_shopping_cart',
    )
    tags = rest_framework.CharFilter(
        field_name='tags__slug',
        lookup_expr='iexact',
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags'
        )

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favourites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
