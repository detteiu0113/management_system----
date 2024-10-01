from datetime import date

from django.db import models
from django.utils import timezone

from utils.choices import GRADE_CHOICES, SCHOOL_CHOICES

class Student(models.Model):
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    birth_date = models.DateField(blank=True, null=True)
    elementary_school = models.CharField(max_length=100, blank=True, null=True) # 小学校
    school = models.IntegerField(choices=SCHOOL_CHOICES, blank=True, null=True) # 中学
    high_school = models.CharField(max_length=100, blank=True, null=True) # 高校
    enrollment_date = models.DateField(default=timezone.now, blank=True, null=True) # 入塾日
    grade = models.IntegerField(choices=GRADE_CHOICES, blank=True, null=True) # 現在の学年
    is_elementary_school = models.BooleanField(default=False) # 小学生かどうか
    is_middle_school = models.BooleanField(default=False) # 中学生かどうか
    is_high_school = models.BooleanField(default=False) #　高校生かどうか
    is_on_leave = models.BooleanField(default=False) # 休塾しているかどうか
    is_withdrawn = models.BooleanField(default=False) # 退塾しているかどうか
    is_planning_to_withdraw = models.BooleanField(default=False) # 年度末に退塾するかどうか
    is_upgraded = models.BooleanField(default=False) # 年度切り替えの処理が完了しているかどうか

    def __str__(self):
        return f'{self.last_name} {self.first_name}'
    
    def test_update_grade(self):
        self.grade += 1
        self.save() 

    # 誕生日から学年を更新するメソッド
    def update_grade(self):
        if self.birth_date:
            # Get today's date
            today = date.today()
            # Determine the current academic year
            if today.month >= 3:
                current_year = today.year
            else:
                current_year = today.year - 1
            # Calculate the academic year the student is in based on birth date
            if self.birth_date.month >= 4:
                birth_year = self.birth_date.year
            else:
                birth_year = self.birth_date.year + 1
            age_in_grade = current_year - birth_year - 6

            # Update the grade based on age
            if age_in_grade >= 1 and age_in_grade <= 6:
                self.grade = age_in_grade
                self.is_elementary_school = True
                self.is_middle_school = False
                self.is_high_school = False
            elif age_in_grade >= 7 and age_in_grade <= 9:
                self.grade = age_in_grade
                self.is_elementary_school = False
                self.is_middle_school = True
                self.is_high_school = False
            elif age_in_grade >= 10 and age_in_grade <= 12:
                self.grade = age_in_grade
                self.is_elementary_school = False
                self.is_middle_school = False
                self.is_high_school = True
            else:
                # Handle special cases here
                pass
            # Save the updated instance
            self.save()

class StudentNotable(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    notable = models.TextField()
    # 遅延評価
    writer = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    