import csv
import io
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand
from registry.models import PhoneCode

CSV_URLS = [
    "https://opendata.digital.gov.ru/downloads/ABC-3xx.csv",
    "https://opendata.digital.gov.ru/downloads/ABC-4xx.csv",
    "https://opendata.digital.gov.ru/downloads/ABC-8xx.csv",
    "https://opendata.digital.gov.ru/downloads/DEF-9xx.csv",
]

class Command(BaseCommand):
    help = "Импортирует реестр номеров из Минцифры"

    def handle(self, *args, **kwargs):
        self.stdout.write("Начинается импорт данных...")

        PhoneCode.objects.all().delete()
        count = 0

        for url in CSV_URLS:
            self.stdout.write(f"Загрузка: {url}")
            try:
                req = Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
                    }
                )
                response = urlopen(req)
                csv_data = io.TextIOWrapper(response, encoding='utf-8')
                reader = csv.DictReader(csv_data, delimiter=';')

                for row in reader:
                    try:
                        PhoneCode.objects.create(
                            code=row['Код оператора'].strip(),
                            start=int(row['Диапазон с']),
                            end=int(row['Диапазон по']),
                            capacity=int(row['Емкость']),
                            operator=row['Наименование оператора'].strip(),
                            region=row.get('Наименование региона', '').strip(),
                            inn=row['ИНН оператора'].strip()
                        )
                        count += 1
                    except Exception as e:
                        self.stderr.write(f"Ошибка в строке: {row}\n{e}")
            except Exception as e:
                self.stderr.write(f"Ошибка при загрузке {url}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(f"Импортировано записей: {count}"))
