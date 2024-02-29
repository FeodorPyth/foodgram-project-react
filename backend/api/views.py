from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from djoser.serializers import SetPasswordSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination

from recipes.models import (
    Tag,
    Recipe,
    Ingredient,
    RecipeIngredient,
    Favourite,
    ShoppingCart,
    Subscriptions,
)
from users.models import User
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    CustomUserCreateSerializer,
    UserReadSerializer,
    RecipeReadSerializer,
    RecipeForSubscriptionsSerializer,
    SubscriptionsSerializer,
    RecipeCreateSerializer,
    RecipeFavoriteSerializer,
    RecipeShoppingCartSerializer,
)
from .filters import RecipeViewSetFilter
from .pagintation import CustomPagination
from foodgram.settings import (
    URL_PATH_NAME,
    URL_PATH_PASSWORD,
    URL_PATH_SUBSCRIPTIONS,
    URL_PATH_SUBSCRIBE,
    URL_PATH_FAVORITE,
    URL_PATH_SHOPPING_CART,
)


class TagViewSet(ReadOnlyModelViewSet):
    """
    """
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    """
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None


class UserViewSet(ModelViewSet):
    """
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

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
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False,
            methods=['POST'],
            url_path=URL_PATH_PASSWORD,
            url_name=URL_PATH_PASSWORD,
            permission_classes=(IsAuthenticated,),
            pagination_class=None)
    def set_password(self, request, *args, **kwargs):
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
        users = User.objects.filter(
            following_subscriptions__follower=request.user
        )
        single_page = self.paginate_queryset(users)
        serializer = SubscriptionsSerializer(
            single_page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['POST', 'DELETE'],
            url_path=URL_PATH_SUBSCRIBE,
            url_name=URL_PATH_SUBSCRIBE,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, *args, **kwargs):
        following_user = get_object_or_404(User, id=kwargs['pk'])

        if request.method == 'POST':
            serializer = SubscriptionsSerializer(
                following_user,
                data=request.data,
                context={"request": request}
            )
            if serializer.is_valid(raise_exception=True):
                Subscriptions.objects.create(
                    follower=request.user,
                    following=following_user
                )
                serializer.save()
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':        
            subscription = get_object_or_404(
                Subscriptions,
                follower=request.user,
                following=User.objects.get(pk=self.kwargs.get('pk'))
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeViewSetFilter
    http_method_names = ['get', 'post', 'delete', 'patch']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeReadSerializer

    @action(detail=True,
            methods=['POST', 'DELETE'],
            url_path=URL_PATH_FAVORITE,
            url_name=URL_PATH_FAVORITE,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, *args, **kwargs):
        favorited_recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            if Favourite.objects.filter(
                user=request.user,
                recipe=favorited_recipe
            ).exists():
                return Response(
                    {'message': 'Этот рецепт уже добавлен в избранное!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeFavoriteSerializer(
                favorited_recipe,
                data=request.data,
                context={"request": request}
            )
            if serializer.is_valid(raise_exception=True):
                Favourite.objects.create(
                    user=request.user,
                    recipe=favorited_recipe
                )
                serializer.save(user=request.user, recipe=favorited_recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not Favourite.objects.filter(
                user=request.user,
                recipe=favorited_recipe
            ).exists():
                return Response(
                    {'message': 'Объекта в избранном не существует!'},
                    status=status.HTTP_404_NOT_FOUND
                )
            favorites = get_object_or_404(
                Favourite,
                user=request.user,
                recipe=favorited_recipe
            )
            favorites.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['POST', 'DELETE'],
            url_path=URL_PATH_SHOPPING_CART,
            url_name=URL_PATH_SHOPPING_CART,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, *args, **kwargs):
        shopping_cart_recipe = get_object_or_404(Recipe, id=kwargs['pk'])

        if request.method == 'POST':
            if ShoppingCart.objects.filter(
                user=request.user,
                recipe=shopping_cart_recipe
            ).exists():
                return Response(
                    {'message': 'Этот рецепт уже добавлен в список покупок!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeShoppingCartSerializer(
                shopping_cart_recipe,
                data=request.data,
                context={"request": request}
            )
            if serializer.is_valid(raise_exception=True):
                ShoppingCart.objects.create(
                    user=request.user,
                    recipe=shopping_cart_recipe
                )
                serializer.save(user=request.user, recipe=shopping_cart_recipe)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not ShoppingCart.objects.filter(
                user=request.user,
                recipe=shopping_cart_recipe
            ).exists():
                return Response(
                    {'message': 'Объекта в списке покупок не существует!'},
                    status=status.HTTP_404_NOT_FOUND
                )
            shopping_cart = get_object_or_404(
                ShoppingCart,
                user=request.user,
                recipe=shopping_cart_recipe
            )
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
