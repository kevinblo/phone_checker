import csv
import io
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from django.core.management.base import BaseCommand
from registry.models import PhoneCode


CSV_URLS = [
    "https://opendata.digital.gov.ru/downloads/ABC-3xx.csv",
    # "https://opendata.digital.gov.ru/downloads/ABC-4xx.csv",
    # "https://opendata.digital.gov.ru/downloads/ABC-8xx.csv",
    # "https://opendata.digital.gov.ru/downloads/DEF-9xx.csv",
]


class Command(BaseCommand):
    help = "Импортирует номера с учётом переносов внутри диапазонов"

    def handle(self, *args, **kwargs):
        self.stdout.write("▶️ Импорт с поддержкой разбиения пулов...")

        created = 0
        updated = 0
        skipped = 0
        split_applied = 0

        for url in CSV_URLS:
            self.stdout.write(f"📥 Загрузка: {url}")
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
                response = urlopen(req)
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
                        capacity = int(get_field(row, 'Емкость'))
                        operator = get_field(row, 'Наименование оператора', 'Оператор')
                        region = get_field(row, 'Наименование региона', 'Регион')
                        inn = get_field(row, 'ИНН оператора', 'ИНН')

                        # ищем пересечения с текущими
                        overlapping = PhoneCode.objects.filter(
                            code=code,
                            start__lte=end,
                            end__gte=start
                        )

                        if not overlapping.exists():
                            # нет конфликтов — создаём
                            PhoneCode.objects.create(
                                code=code, start=start, end=end,
                                capacity=capacity, operator=operator,
                                region=region, inn=inn
                            )
                            created += 1
                            continue

                        # обрабатываем все перекрытия
                        for existing in overlapping:
                            # если полностью совпадает и ничего не изменилось — пропускаем
                            if (
                                    existing.start == start and
                                    existing.end == end and
                                    existing.capacity == capacity and
                                    existing.operator == operator and
                                    existing.region == region and
                                    existing.inn == inn
                            ):
                                skipped += 1
                                break

                            # удаляем перекрытие
                            existing.delete()

                            # часть до переноса
                            if existing.start < start:
                                PhoneCode.objects.create(
                                    code=code, start=existing.start, end=start - 1,
                                    capacity=existing.capacity,
                                    operator=existing.operator,
                                    region=existing.region,
                                    inn=existing.inn
                                )
                                split_applied += 1

                            # часть переноса (новый оператор)
                            PhoneCode.objects.create(
                                code=code, start=start, end=end,
                                capacity=capacity, operator=operator,
                                region=region, inn=inn
                            )
                            split_applied += 1

                            # часть после переноса
                            if existing.end > end:
                                PhoneCode.objects.create(
                                    code=code, start=end + 1, end=existing.end,
                                    capacity=existing.capacity,
                                    operator=existing.operator,
                                    region=existing.region,
                                    inn=existing.inn
                                )
                                split_applied += 1

                            break  # один конфликт — один раз

                    except Exception as e:
                        self.stderr.write(f"❌ Ошибка в строке: {row}\n{e}")

            except (URLError, HTTPError) as e:
                self.stderr.write(f"⛔ Ошибка при загрузке {url}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(
            f"✅ Импорт завершён: создано — {created}, обновлено — {updated}, "
            f"пропущено — {skipped}, разбиений — {split_applied}"
        ))
