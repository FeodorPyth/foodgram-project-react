from django.conf import settings
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

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
from foodgram.settings import (
    URL_PATH_DOWNLOAD_SHOPPING_CART,
    URL_PATH_FAVORITE,
    URL_PATH_NAME,
    URL_PATH_PASSWORD,
    URL_PATH_SHOPPING_CART,
    URL_PATH_SUBSCRIBE,
    URL_PATH_SUBSCRIPTIONS,
)
from recipes.models import (
    Favourite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscriptions,
    Tag,
)
from users.models import User


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
    POST-запрос по id - добавление нового ингредиента.
    DELETE-запрос по id - удаление выбранного ингредиента.
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
            methods=['POST', 'DELETE'],
            url_path=URL_PATH_SUBSCRIBE,
            url_name=URL_PATH_SUBSCRIBE,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, *args, **kwargs):
        """
        POST-запрос по id и subscribe - подписаться на пользователя.
        POST-запрос по id и subscribe - отписаться от пользователя.
        """
        following_user = get_object_or_404(User, id=kwargs['pk'])
        recipes_limit = request.query_params.get('recipes_limit')

        if request.method == 'POST':
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
        if request.method == 'DELETE':
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
            methods=['POST', 'DELETE'],
            url_path=URL_PATH_FAVORITE,
            url_name=URL_PATH_FAVORITE,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, *args, **kwargs):
        """
        POST-запрос по id и favorite - добавление рецепта в избранное.
        DELETE-запрос по id и favorite - удаление рецепта из избранного.
        """
        favorited_recipe = Recipe.objects.filter(id=kwargs['pk']).first()

        if request.method == 'POST':
            if not favorited_recipe:
                return Response(
                    {'message': 'Рецепт не существует!'},
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
            favorited_recipe = get_object_or_404(
                Recipe,
                pk=request.parser_context['kwargs'].get('pk')
            )
            favorites = Favourite.objects.filter(
                user=request.user,
                recipe=favorited_recipe
            ).first()
            if not favorites:
                return Response(
                    {"error": "Объекта в избранном не существует!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorites.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=['POST', 'DELETE'],
            url_path=URL_PATH_SHOPPING_CART,
            url_name=URL_PATH_SHOPPING_CART,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, *args, **kwargs):
        """
        POST-запрос по id и shopping_cart - добавить рецепт в список покупок.
        DELETE-запрос по id и shopping_cart - удалить рецепт из списка покупок.
        """
        shopping_cart_recipe = Recipe.objects.filter(id=kwargs['pk']).first()

        if request.method == 'POST':
            if not shopping_cart_recipe:
                return Response(
                    {'message': 'Рецепт не существует!'},
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
            shopping_cart_recipe = get_object_or_404(
                Recipe,
                pk=request.parser_context['kwargs'].get('pk')
            )
            shopping_cart = ShoppingCart.objects.filter(
                user=request.user,
                recipe=shopping_cart_recipe
            ).first()
            if not shopping_cart:
                return Response(
                    {"error": "Объекта в списке покупок не существует!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['GET'],
            url_path=URL_PATH_DOWNLOAD_SHOPPING_CART,
            url_name=URL_PATH_DOWNLOAD_SHOPPING_CART,
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request, *args, **kwargs):
        """GET-запрос по download_shopping_cart - скачать список покупок."""
        user = User.objects.get(id=self.request.user.pk)
        if user.shopping_cart.exists():
            user = request.user
            user_shopping_cart = ShoppingCart.objects.filter(user=user)
            unique_ingredients = RecipeIngredient.objects.filter(
                recipe__in=user_shopping_cart.values('recipe')
            ).values(
                'ingredient__name', 'ingredient__measurement_unit'
                ).annotate(
                    total_quantity=Sum('amount')
                    )

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = (
                'attachment; filename="shopping_cart.pdf"'
            )

            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            p.setFillColorRGB(0.9, 0.9, 0.9)  # Устанавливаем серый цвет фона
            p.rect(-1, 0, 600, 843, fill=1)  # Ставим размер рамки фона
            p.setFillColorRGB(0, 0, 0)  # Делаем цвет текста - черным

            pdfmetrics.registerFont(
                TTFont(
                    'Arial',
                    str(settings.BASE_DIR / 'fonts/caviar-dreams.ttf')
                )
            )
            p.setFont("Arial", 12)

            y_position = 800
            p.drawString(250, y_position, "Список покупок:")

            y_position -= 20
            for ingredient in unique_ingredients:
                p.drawString(
                    100,
                    y_position,
                    f"{ingredient['ingredient__name']} - "
                    f"{ingredient['total_quantity']} "
                    f"{ingredient['ingredient__measurement_unit']}"
                )
                y_position -= 20

            p.line(100, y_position, 500, y_position)

            y_position -= 20
            p.drawString(260, y_position, "@foodgram")

            p.showPage()
            p.save()

            pdf = buffer.getvalue()
            buffer.close()

            response.write(pdf)

            return response

        return Response(
            {'message': 'Список покупок пользователя пуст!'},
            status=status.HTTP_404_NOT_FOUND
        )
