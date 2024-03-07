# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter


# def generate_pdf_from_ingredients(ingredients):
#     # Здесь должен быть код для генерации PDF-файла из списка ингредиентов
#     # Предполагается, что у вас есть библиотека для работы с PDF, такая как reportlab
#     # Это примерный код, который нужно будет адаптировать под ваши потребности
#     canv = canvas.Canvas('shopping_cart.pdf', pagesize=letter)
#     canv.setFont('Helvetica', 12)
#     for ingredient in ingredients:
#         canv.drawString(100, 750, ingredient.name)
#         canv.drawString(100, 725, str(ingredient.amount) + ' ' + ingredient.measurement_unit)
#     canv.save()
#     return canv
