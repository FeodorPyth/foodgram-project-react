from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    TagViewSet,
    IngredientViewSet,
    UserViewSet,
    RecipeViewSet,
)


router_v1 = DefaultRouter()
router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')
router_v1.register(r'users', UserViewSet, basename='users')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    url(r'^auth/', include('djoser.urls.authtoken')),
    path(r'', include(router_v1.urls)),
]
