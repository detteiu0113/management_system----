from django.db import models
from accounts.models import CustomUser
from regular_lesson.models import Lesson
from vocabulary_test.models import TestResult
from students.models import Student
 
class Report(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='report')
    homework = models.BooleanField(default=False) # 宿題を出したか
    homework_done = models.BooleanField(default=False) # 宿題をしたか
    unit = models.CharField(max_length=50, blank=True, null=True) # 単元
    behavior = models.TextField(blank=True, null=True) # 授業中の様子
    weakness = models.TextField(blank=True, null=True) # 苦手単元、改善点

    def __str__(self):
        return f'{self.lesson}'