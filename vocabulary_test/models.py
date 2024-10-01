from django.db import models
from students.models import Student

CATEGORY_CHOICES = [
    (1, 'α'),
    (2, 'β'),
]

PROGRAM_CHOICES = [
    (i, f'Program{i}') for i in range(1, 11)
]

COUNT_CHOICES = [
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
]

class TestResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_results')
    date = models.DateField(null=True, blank=True)
    category = models.IntegerField(choices=CATEGORY_CHOICES)
    program = models.IntegerField(choices=PROGRAM_CHOICES)
    fullscore = models.IntegerField(null=True, blank=True)
    score=models.IntegerField(null=True, blank=True)
    count= models.IntegerField(choices=COUNT_CHOICES)

    def __str__(self):
        return f'{self.student} {self.get_program_display()} {self.get_category_display()} {self.count}回目'
    