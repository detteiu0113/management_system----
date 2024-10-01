from django.contrib.auth.models import AbstractUser
from django.db import models
from students.models import Student
from utils.choices import GRADE_CHOICES, SUBJECT_CHOICES

class CustomUser(AbstractUser):
    is_owner = models.BooleanField(default=False)
    is_parent = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

    # 以下はAbstractUserのフィールドをオーバーライドしてカスタムフィールドを持つようにする
    username = models.CharField(max_length=150, unique=True)  # ユーザー名
    email = models.EmailField(unique=False, blank=True)  # メールアドレス
    first_name = models.CharField(max_length=30, blank=True)  # ユーザーのファーストネーム
    last_name = models.CharField(max_length=150, blank=True)  # ユーザーのラストネーム
    date_joined = models.DateTimeField(auto_now_add=True)  # ユーザーがサイトに参加した日時
    is_active = models.BooleanField(default=True)  # アカウントがアクティブかどうか
    is_staff = models.BooleanField(default=False)  # スタッフ権限を持つかどうか
    is_superuser = models.BooleanField(default=False)  # スーパーユーザーかどうか

    def __str__(self):
        
        # 開発用
        if self.first_name and self.last_name:
            name = self.last_name + ' ' + self.first_name
        else:
            name = self.username
        return name

        # 本来はこちらを使用
        # return f'{self.last_name} {self.first_name}'

class OwnerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='owner_profile')

    def __str__(self):
        return f'{self.user}'

class TeacherProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    is_withdrawn = models.BooleanField(default=False)
    
    def __str__(self):
        return f'{self.user}'
    
# 未使用
class TeachingPermission(models.Model):
    teacher_profile = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, blank=True)
    grade = models.IntegerField(choices=GRADE_CHOICES, blank=True)
    subject = models.IntegerField(choices=SUBJECT_CHOICES, blank=True)
    is_teaching = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.teacher_profile} - {self.grade} - {self.subject}'

class ParentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='parent_profile')
    student = models.ManyToManyField(Student, blank=True, related_name='parent')
    # ユーザーの切り替えに使用
    current_student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='parent_profiles')

    def __str__(self):
        return f'{self.user} - {self.student} - {self.current_student}'
    
