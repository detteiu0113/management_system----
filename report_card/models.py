from django.db import models
from students.models import Student

SEMESTER_CHOICES = (
    (1, '1年1学期'),
    (2, '1年2学期'),
    (3, '1年3学期'),
    (4, '2年1学期'),
    (5, '2年2学期'),
    (6, '2年3学期'),
    (7, '3年1学期'),
    (8, '3年2学期'),
)

SUBJECT_CHOICES = (
    (1, '国語'),
    (2, '数学'),
    (3, '英語'),
    (4, '社会'),
    (5, '理科'),
    (6, '音楽'),
    (7, '美術'),
    (8, '体育'),
    (9, '技家'),
)

class ReportGrade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE) # 生徒
    semester = models.IntegerField(choices=SEMESTER_CHOICES) # 学期
    subject = models.IntegerField(choices=SUBJECT_CHOICES)  # 科目
    value = models.IntegerField(null=True, blank=True)  # 評価

    def __str__(self):
        return f'{self.student} - {self.get_semester_display()} - {self.get_subject_display()}: {self.value}'
