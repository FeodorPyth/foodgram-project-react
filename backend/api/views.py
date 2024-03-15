from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from foodgram.constants import (
    URL_PATH_DOWNLOAD_SHOPPING_CART,
    URL_PATH_FAVORITE,
    URL_PATH_NAME,
    URL_PATH_PASSWORD,
    URL_PATH_SHOPPING_CART,
    URL_PATH_SUBSCRIBE,
    URL_PATH_SUBSCRIPTIONS
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Subscriptions,
    Tag
)
from users.models import User
from .filters import IngredientViewSetFilter, RecipeViewSetFilter
from .pagintation import CustomPagination
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import (
    CustomUserCreateSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeFavoriteSerializer,
    RecipeReadSerializer,
    RecipeShoppingCartSerializer,
    SubscriptionsSerializer,
    TagSerializer,
    UserReadSerializer,
)
from .services import (
    PHRASE_FOR_FAVORITE,
    PHRASE_FOR_SHOPPING_CART,
    draw_pdf_file,
    get_delete_method_remove_object,
    get_post_method_add_object,
    get_shopping_cart_ingredients
)


class TagViewSet(ReadOnlyModelViewSet):
    """
    Вьюсет для тегов.
    GET-запрос - получение тегов.
    GET-запрос по id - получение конкретного тега.
    """
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    Вьюсет для ингредиентов.
    GET-запрос - получение ингредиентов.
    GET-запрос по id - получение конкретного ингредиента.
    """
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = (IngredientViewSetFilter,)
    search_fields = ('^name',)


class UserViewSet(ModelViewSet):
    """
    Вьюсет для пользователей.
    GET-запрос - получение списка пользователей.
    POST-запрос - регистрация нового пользователя.
    GET-запрос по id - получение профиля пользователя.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        return CustomUserCreateSerializer

    @action(detail=False,
            methods=['GET'],
            url_path=URL_PATH_NAME,
            url_name=URL_PATH_NAME,
            permission_classes=(IsAuthenticated,),
            pagination_class=None)
    def me(self, request):
        """GET-запрос по me - получение конкретного пользователя."""
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False,
            methods=['POST'],
            url_path=URL_PATH_PASSWORD,
            url_name=URL_PATH_PASSWORD,
            permission_classes=(IsAuthenticated,),
            pagination_class=None)
    def set_password(self, request, *args, **kwargs):
        """POST-запрос по set_password - смена пароля."""
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            self.request.user.set_password(serializer.data["new_password"])
            self.request.user.save()
            return Response(
                {"message": "Смена пароля прошла успешно!"},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,
            methods=['GET'],
            url_path=URL_PATH_SUBSCRIPTIONS,
            url_name=URL_PATH_SUBSCRIPTIONS,
            permission_classes=(IsAuthenticated,),
            pagination_class=CustomPagination)
    def subscriptions(self, request):
        """GET-запрос по subscriptions - получение списка подписчиков."""
        recipes_limit = request.query_params.get('recipes_limit')
        users = User.objects.filter(
            following_subscriptions__follower=request.user
        )
        single_page = self.paginate_queryset(users)
        serializer = SubscriptionsSerializer(
            single_page,
            many=True,
            context={"request": request, "recipes_limit": recipes_limit}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['POST'],
            url_path=URL_PATH_SUBSCRIBE,
            url_name=URL_PATH_SUBSCRIBE,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, *args, **kwargs):
        """POST-запрос по id и subscribe - подписаться на пользователя."""
        following_user = get_object_or_404(User, id=kwargs['pk'])
        recipes_limit = request.query_params.get('recipes_limit')
        serializer = SubscriptionsSerializer(
            following_user,
            data=request.data,
            context={"request": request, "recipes_limit": recipes_limit}
        )
        if serializer.is_valid(raise_exception=True):
            Subscriptions.objects.create(
                follower=request.user,
                following=following_user
            )
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, *args, **kwargs):
        """DELETE-запрос по id и subscribe - отписаться от пользователя."""
        following_user = get_object_or_404(User, id=kwargs['pk'])
        subscription = Subscriptions.objects.filter(
            follower=request.user,
            following=following_user
        ).first()
        if not subscription:
            return Response(
                {"error": "Подписка не существует."},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(ModelViewSet):
    """
    Вьюсет для рецептов.
    GET-запрос - получение списка рецептов.
    POST-запрос - создание нового рецепта.
    GET-запрос по id - получение рецепта.
    PATCH-запрос по id - обновление рецепта.
    DELETE-запрос по id - удаление рецепта.
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrAdminOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeViewSetFilter
    http_method_names = ['get', 'post', 'delete', 'patch']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeCreateSerializer

    @action(detail=True,
            methods=['POST'],
            url_path=URL_PATH_FAVORITE,
            url_name=URL_PATH_FAVORITE,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, *args, **kwargs):
        """POST-запрос по id и favorite - добавление рецепта в избранное."""
        favorited_recipe = Recipe.objects.filter(id=kwargs['pk']).first()
        return get_post_method_add_object(
            request,
            favorited_recipe,
            RecipeFavoriteSerializer,
            Favorite,
            request.user,
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, *args, **kwargs):
        """DELETE-запрос по id и favorite - удаление рецепта из избранного."""
        return get_delete_method_remove_object(
            request,
            Recipe,
            Favorite,
            request.user,
            PHRASE_FOR_FAVORITE,
        )

    @action(detail=True,
            methods=['POST'],
            url_path=URL_PATH_SHOPPING_CART,
            url_name=URL_PATH_SHOPPING_CART,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, *args, **kwargs):
        """POST-запрос по id и shopping_cart - добавить рецепт в покупки."""
        shopping_cart_recipe = Recipe.objects.filter(id=kwargs['pk']).first()
        return get_post_method_add_object(
            request,
            shopping_cart_recipe,
            RecipeShoppingCartSerializer,
            ShoppingCart,
            request.user,
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, *args, **kwargs):
        """DELETE-запрос по id и shopping_cart - удалить рецепт из покупок."""
        return get_delete_method_remove_object(
            request,
            Recipe,
            ShoppingCart,
            request.user,
            PHRASE_FOR_SHOPPING_CART,
        )

    @action(detail=False,
            methods=['GET'],
            url_path=URL_PATH_DOWNLOAD_SHOPPING_CART,
            url_name=URL_PATH_DOWNLOAD_SHOPPING_CART,
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, *args, **kwargs):
        """GET-запрос по download_shopping_cart - скачать список покупок."""
        user = User.objects.get(id=self.request.user.pk)
        if user.shoppingcart_user.exists():
            unique_ingredients = get_shopping_cart_ingredients(request.user)
            return draw_pdf_file(unique_ingredients=unique_ingredients)
        return Response(
            {'message': 'Список покупок пользователя пуст!'},
            status=status.HTTP_404_NOT_FOUND
        )
