import csv
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('ingredients.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            next(reader, None)  # Пропускаем заголовок

            for row in reader:
                name, measurement_unit = row
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit,
                )

                if created:
                    print(f'Created ingredient: {name}')
                else:
                    print(f'Updated ingredient: {name}')
