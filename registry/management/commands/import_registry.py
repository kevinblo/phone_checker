import csv
import io
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from django.core.management.base import BaseCommand
from registry.models import PhoneCode

CSV_URLS = [
    "https://opendata.digital.gov.ru/downloads/ABC-3xx.csv",
    "https://opendata.digital.gov.ru/downloads/ABC-4xx.csv",
    "https://opendata.digital.gov.ru/downloads/ABC-8xx.csv",
    "https://opendata.digital.gov.ru/downloads/DEF-9xx.csv",
]

class Command(BaseCommand):
    help = "Импортирует/обновляет данные с проверкой изменений"

    def handle(self, *args, **kwargs):
        self.stdout.write("Импорт с проверкой изменений...")

        created = 0
        updated = 0
        skipped = 0

        for url in CSV_URLS:
            self.stdout.write(f"Загрузка: {url}")
            try:
                req = Request(
                    url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/113.0.0.0 Safari/537.36"
                        )
                    }
                )
                response = urlopen(req)  # 👈 таймаут удалён
                csv_data = io.TextIOWrapper(response, encoding='utf-8')
                reader = csv.DictReader(csv_data, delimiter=';')

                def get_field(row, *names):
                    for name in names:
                        if name in row:
                            return row[name].strip()
                    return ''

                for row in reader:
                    try:
                        code = get_field(row, 'Код оператора', 'АВС/ DEF', '\ufeffАВС/ DEF')
                        start = int(get_field(row, 'Диапазон с', 'От'))
                        end = int(get_field(row, 'Диапазон по', 'До'))

                        new_data = {
                            'capacity': int(get_field(row, 'Емкость')),
                            'operator': get_field(row, 'Наименование оператора', 'Оператор'),
                            'region': get_field(row, 'Наименование региона', 'Регион'),
                            'inn': get_field(row, 'ИНН оператора', 'ИНН'),
                        }

                        try:
                            obj = PhoneCode.objects.get(code=code, start=start, end=end)
                            changed = False
                            for field, new_value in new_data.items():
                                if getattr(obj, field) != new_value:
                                    setattr(obj, field, new_value)
                                    changed = True
                            if changed:
                                obj.save()
                                updated += 1
                            else:
                                skipped += 1
                        except PhoneCode.DoesNotExist:
                            PhoneCode.objects.create(
                                code=code,
                                start=start,
                                end=end,
                                **new_data
                            )
                            created += 1

                    except Exception as e:
                        self.stderr.write(f"Ошибка в строке: {row}\n{e}")

            except (URLError, HTTPError) as e:
                self.stderr.write(f"Ошибка при загрузке {url}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(
            f"Импорт завершён: новых — {created}, обновлено — {updated}, без изменений — {skipped}"
        ))
