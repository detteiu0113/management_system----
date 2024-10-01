from django.db import models
from students.models import Student

# Create your models here.
class Event(models.Model):
    title = models.CharField(max_length=20, blank=True, null=True)
    date = models.DateField()
    hidden = models.ManyToManyField(Student, blank=True)
    # 休校の場合はTrueを選択
    is_closure = models.BooleanField(default=False)
    # 編集不可の場合はTrueを選択
    is_fixed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.date} - {self.title}'
        