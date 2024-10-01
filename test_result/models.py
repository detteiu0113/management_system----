from django.db import models
from utils.choices import SCHOOL_CHOICES, GRADE_CHOICES
from students.models import Student

class AverageScore(models.Model):
    test_name = models.CharField(max_length=20)
    school = models.IntegerField(choices=SCHOOL_CHOICES)
    grade = models.IntegerField(choices=GRADE_CHOICES)
    date = models.DateField(blank=True, null=True)
    jap = models.FloatField(blank=True, null=True)
    mat = models.FloatField(blank=True, null=True)
    soc = models.FloatField(blank=True, null=True)
    sci = models.FloatField(blank=True, null=True)
    eng = models.FloatField(blank=True, null=True)
    five_total = models.FloatField(blank=True, null=True)
    mus = models.FloatField(blank=True, null=True)
    art = models.FloatField(blank=True, null=True)
    phy = models.FloatField(blank=True, null=True)
    tec = models.FloatField(blank=True, null=True)
    nine_total = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f'{self.test_name} {self.get_school_display()} {self.get_grade_display()} {self.date}'

class TestResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    average_score = models.ForeignKey(AverageScore, on_delete=models.CASCADE)
    jap = models.IntegerField(blank=True, null=True)
    mat = models.IntegerField(blank=True, null=True)
    soc = models.IntegerField(blank=True, null=True)
    sci = models.IntegerField(blank=True, null=True)
    eng = models.IntegerField(blank=True, null=True)
    mus = models.IntegerField(blank=True, null=True)
    art = models.IntegerField(blank=True, null=True)
    phy = models.IntegerField(blank=True, null=True)
    tec = models.IntegerField(blank=True, null=True)
    jap_rank = models.IntegerField(blank=True, null=True)
    mat_rank = models.IntegerField(blank=True, null=True)
    soc_rank = models.IntegerField(blank=True, null=True)
    sci_rank = models.IntegerField(blank=True, null=True)
    eng_rank = models.IntegerField(blank=True, null=True)
    five_total_rank = models.IntegerField(blank=True, null=True)
    mus_rank = models.IntegerField(blank=True, null=True)
    art_rank = models.IntegerField(blank=True, null=True)
    phy_rank = models.IntegerField(blank=True, null=True)
    tec_rank = models.IntegerField(blank=True, null=True)
    nine_total_rank = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.average_score.test_name