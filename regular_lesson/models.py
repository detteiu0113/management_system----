from django.db import models
from students.models import Student
from special_lesson.models import SpecialLessonAdmin
from utils.choices import DAY_CHOICES, TIME_CHOICES, SUBJECT_CHOICES, GRADE_CHOICES, SPECIAL_TIME_CHOICES

class RegularLessonAdmin(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    grade = models.IntegerField(choices=GRADE_CHOICES, blank=True, null=True)
    subject = models.IntegerField(choices=SUBJECT_CHOICES)
    day = models.IntegerField(choices=DAY_CHOICES)
    time = models.IntegerField(choices=TIME_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_upgraded = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.student} {self.get_subject_display()} {self.get_day_display()} {self.get_time_display()}'
    
class Lesson(models.Model):
    regular = models.ForeignKey(RegularLessonAdmin, on_delete=models.CASCADE, blank=True, null=True)
    special = models.ForeignKey(SpecialLessonAdmin, on_delete=models.CASCADE, blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=True, null=True)
    grade = models.IntegerField(choices=GRADE_CHOICES, blank=True, null=True)
    subject = models.IntegerField(choices=SUBJECT_CHOICES, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    time = models.IntegerField(choices=SPECIAL_TIME_CHOICES+TIME_CHOICES, blank=True, null=True)
    rescheduled_date = models.DateField(blank=True, null=True) # 振替先の日付
    rescheduled_time = models.IntegerField(choices=SPECIAL_TIME_CHOICES+TIME_CHOICES, blank=True, null=True) # 振替先の時間
    is_regular = models.BooleanField(default=False) # 通常授業か講習授業か判別
    is_temporaly = models.BooleanField(default=False) # 臨時授業の場合はTrue
    is_absence = models.BooleanField(default=False) # 欠席した場合はTrueでその後振替がされる
    is_unauthorized_absence = models.BooleanField(default=False) # 無断欠席の場合はTrueで振替がされない
    is_rescheduled = models.BooleanField(default=False) # 振替先が決まった場合はTrue
    is_reported = models.BooleanField(default=False) # 報告書が送信されればTrue

    def __str__(self):
        return f'{self.student} {self.get_subject_display()} {self.date} {self.get_time_display()}'

    class Meta:
        ordering = ('date',)
    
    