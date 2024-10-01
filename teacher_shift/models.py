from django.db import models
from accounts.models import CustomUser
from utils.choices import DAY_CHOICES, TIME_CHOICES, SPECIAL_TIME_CHOICES, SALARY_CHOICES

# Create your models here.
class FixedShift(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
    day = models.IntegerField(choices=DAY_CHOICES)
    time = models.IntegerField(choices=TIME_CHOICES)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_upgraded = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.teacher} - {self.get_day_display()} - {self.get_time_display()}'
    
# 実質的にspecial_shift
class TemporalyShift(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    time = models.IntegerField(choices=SPECIAL_TIME_CHOICES+TIME_CHOICES)
    is_special = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.teacher} - {self.date} - {self.get_time_display()}'
    
# timeフィールドを追加するべき?
class TeacherShift(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True)
    fixed_shift = models.ForeignKey(FixedShift, on_delete=models.CASCADE, blank=True, null=True)
    temporaly_shift = models.ForeignKey(TemporalyShift, on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    time = models.IntegerField(choices=SPECIAL_TIME_CHOICES+TIME_CHOICES, blank=True, null=True)
    is_fixed = models.BooleanField(default=False)
    
    def __str__(self):
        if self.is_fixed:
            return f'{self.fixed_shift} - {self.date}'
        else:
            return f'{self.temporaly_shift} - {self.date}'
        
class Salary(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    cost_name = models.IntegerField(choices=SALARY_CHOICES, blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    date = models.DateField()

