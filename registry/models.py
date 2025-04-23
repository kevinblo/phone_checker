# apps/registry/models.py
from django.db import models


class PhoneCode(models.Model):
    code = models.IntegerField()
    start = models.BigIntegerField()
    end = models.BigIntegerField()
    capacity = models.IntegerField()
    operator = models.CharField(max_length=1500)
    region = models.CharField(max_length=1500, null=True, blank=True)
    inn = models.CharField(max_length=12)

    def __str__(self):
        return f"{self.code}: {self.operator} ({self.start}-{self.end})"
