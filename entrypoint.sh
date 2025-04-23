#!/bin/bash

python manage.py migrate

count=$(python manage.py shell -c "import django; django.setup(); from registry.models import PhoneCode; print(PhoneCode.objects.count())" | tail -n 1)

if [ "$count" -eq 0 ] 2>/dev/null; then
    echo "Таблица пуста — импортирую данные..."
    python manage.py import_registry
else
    echo "В таблице уже есть записи ($count), импорт не нужен."
fi

crontab /app/cron/crontab.txt

exec "$@"
