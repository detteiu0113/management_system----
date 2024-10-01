from django.db import models
from students.models import Student
from accounts.models import CustomUser
from utils.choices import GRADE_CHOICES, SUBJECT_CHOICES, TIME_CHOICES, SPECIAL_TIME_CHOICES
from django.core.exceptions import ValidationError

class SpecialLesson(models.Model):
    name = models.CharField(max_length=10)
    start_date = models.DateField()
    end_date = models.DateField()
    is_extend = models.BooleanField(default=False)

    def __str__(self):
        
        return f'{self.name} {self.start_date} - {self.end_date}'
    
class SpecialLessonAdmin(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    grade = models.IntegerField(choices=GRADE_CHOICES, blank=True, null=True)
    special_lesson = models.ForeignKey(SpecialLesson, on_delete=models.CASCADE, related_name='special_lesson')
    periods = models.PositiveIntegerField()
    subject = models.IntegerField(choices=SUBJECT_CHOICES)

    def get_referencing_lesson_count(self):
        from regular_lesson.models import Lesson
        return Lesson.objects.filter(special=self).count()

    def __str__(self):
        referencing_lesson_count = self.get_referencing_lesson_count()
        return f'{self.student} {self.get_subject_display()} 選択済みコマ数 {referencing_lesson_count} / {self.periods}コマ'
    

class SpecialLessonStudentRequest(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    special_lesson = models.ForeignKey(SpecialLesson, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True)
    time = models.IntegerField(choices=SPECIAL_TIME_CHOICES+TIME_CHOICES, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f'{self.student}- {self.special_lesson} - {self.date} - {self.get_time_display()}'

class SpecialLessonTeacherRequest(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    special_lesson = models.ForeignKey(SpecialLesson, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True)
    time = models.IntegerField(choices=SPECIAL_TIME_CHOICES+TIME_CHOICES, blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.teacher}- {self.special_lesson} - {self.date} - {self.get_time_display()}'
