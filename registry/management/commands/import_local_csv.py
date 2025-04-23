import csv
from django.core.management.base import BaseCommand
from registry.models import PhoneCode

class Command(BaseCommand):
    help = "Импортирует данные из локального CSV-файла (например, ABC-3xx.csv)"

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str, help='Путь к локальному CSV-файлу')

    def handle(self, *args, **options):
        filepath = options['filepath']
        self.stdout.write(f"Импорт из файла: {filepath}")

        try:
            with open(filepath, newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=';')

                def get_field(row, *names):
                    for name in names:
                        if name in row:
                            return row[name].strip()
                    return ''

                count = 0
                for row in reader:
                    try:
                        code_str = get_field(row, 'Код оператора', 'АВС/ DEF')
                        code = int(code_str) if code_str.isdigit() else None
                        if code is None:
                            raise ValueError(f"Некорректный код: '{code_str}'")

                        start = int(get_field(row, 'Диапазон с', 'От'))
                        end = int(get_field(row, 'Диапазон по', 'До'))
                        capacity = int(get_field(row, 'Емкость'))

                        PhoneCode.objects.create(
                            code=code,
                            start=start,
                            end=end,
                            capacity=capacity,
                            operator=get_field(row, 'Наименование оператора', 'Оператор'),
                            region=get_field(row, 'Наименование региона', 'Регион'),
                            inn=get_field(row, 'ИНН оператора', 'ИНН')
                        )
                        count += 1
                    except Exception as e:
                        self.stderr.write(f"\nОшибка в строке:\n{row}\nПричина: {e}\n")

                self.stdout.write(self.style.SUCCESS(f"Импортировано записей: {count}"))

        except FileNotFoundError:
            self.stderr.write(f"Файл не найден: {filepath}")
        except Exception as e:
            self.stderr.write(f"Ошибка при импорте: {str(e)}")
