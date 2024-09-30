import csv
import os

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Импорт данных из файлов *.csv в БД."""

    help = 'Импорт данных из файла ingredients.csv,\
        importcsv <путь к директории>.'

    def add_arguments(self, parser):
        parser.add_argument(
            'dir', type=str, help='Папка с файлами для импорта данных'
        )

    def get_file(self, dir):
        """Чтение директории."""
        list_dir = os.listdir(dir)
        file = 'ingredients.csv'
        if file not in list_dir:
            raise ValidationError('Файл с данными отсутсвует!')
        return file

    def create_object(self, data):
        """Создание объекта модели."""
        obj, st = Ingredient.objects.get_or_create(**data)
        self.stdout.write(self.style.SUCCESS(f'Объект {obj} создан.'))

    def handle(self, *args, **kwargs):
        dir = kwargs['dir']
        file = self.get_file(dir)
        try:
            with open(dir + '/' + file, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(
                    csvfile, fieldnames=['name', 'measurement_unit']
                )
                for row in reader:
                    try:
                        self.create_object(row)
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f'При импорте произошла ошибка: {e}.\n'
                                f'Проверьте данные: {row}'
                            )
                        )
                        continue
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'При импорте произошла ошибка {e}.')
            )
