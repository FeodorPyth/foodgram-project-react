from io import BytesIO

from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import serializers, status
from rest_framework.response import Response

from recipes.models import RecipeIngredient, ShoppingCart


def draw_pdf_file(unique_ingredients):
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


def get_shopping_cart_ingredients(current_user):
    user = current_user
    user_shopping_cart = ShoppingCart.objects.filter(user=user)
    unique_ingredients = RecipeIngredient.objects.filter(
        recipe__in=user_shopping_cart.values('recipe')
    ).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(
        total_quantity=Sum('amount')
    )
    return unique_ingredients


def get_post_method_add_object(
        request, current_recipe, serializer_class, model, user
):
    if not current_recipe:
        return Response(
            {'message': 'Рецепт не существует!'},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer = serializer_class(
        current_recipe,
        data=request.data,
        context={"request": request}
    )
    if serializer.is_valid(raise_exception=True):
        model.objects.create(
            user=user,
            recipe=current_recipe
        )
        serializer.save(user=user, recipe=current_recipe)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)


def get_delete_method_remove_object(
        request, model_for_check_existence, model_for_deletion, user, phrase
):
    object_check_existence = get_object_or_404(
        model_for_check_existence,
        pk=request.parser_context['kwargs'].get('pk')
    )
    object_for_deletion = model_for_deletion.objects.filter(
        user=user,
        recipe=object_check_existence
    ).first()
    if not object_for_deletion:
        return Response(
            {"error": f"Объекта {phrase} не существует!"},
            status=status.HTTP_400_BAD_REQUEST
        )
    object_for_deletion.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def add_tags_and_ingredients(ingredients, tags, model):
    for ingredient in ingredients:
        RecipeIngredient.objects.update_or_create(
            recipe=model,
            ingredient=ingredient['id'],
            amount=ingredient['amount']
        )
    model.tags.set(tags)


def validate_favorite_shopping_cart(
        self,
        data,
        model,
        phrase,
):
    user = self.context['request'].user
    recipe_id = self.context['request'].parser_context['kwargs'].get('pk')
    if model.objects.filter(
        user=user,
        recipe_id=recipe_id
    ).exists():
        raise serializers.ValidationError(phrase)
    return data


PHRASE_FOR_FAVORITE = 'в избранном'

PHRASE_FOR_SHOPPING_CART = 'в списке покупок'

PHRASE_FOR_VALIDATE_FAVORITE = 'Рецепт уже есть в избранном.'

PHRASE_FOR_VALIDATE_SHOPPING_CART = 'Рецепт уже есть в списке покупок.'
