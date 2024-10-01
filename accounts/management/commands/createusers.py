import os
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import CustomUser, OwnerProfile, TeacherProfile, ParentProfile
from students.models import Student
from shift.models import ShiftTemplate, ShiftTemplateLessonRelation
from report_card.models import ReportGrade, SEMESTER_CHOICES
from report_card.models import SUBJECT_CHOICES as REPORT_SUBJECT_CHOICES
from vocabulary_test.models import TestResult, CATEGORY_CHOICES, PROGRAM_CHOICES, COUNT_CHOICES
from utils.choices import DAY_CHOICES, ROOM_CHOICES, TIME_CHOICES

def create_owner(username, last_name, first_name):
    # ownerの作成
    owner = CustomUser.objects.create(
        last_name=last_name,
        first_name=first_name,
        username=username,
        email=username,
        is_owner=True,
        is_staff=True,
        is_superuser=True)
    owner.set_password(os.environ.get('OWNER_PASSWORD'))
    owner.save()
    
    # owner_profileの作成
    OwnerProfile.objects.create(user=owner)

    # 今年度シフトテンプレートの作成
    day_choices =  [day[0] for day in DAY_CHOICES]
    room_choices = [room[0] for room in ROOM_CHOICES]
    time_choices = [time[0] for time in TIME_CHOICES]

    for day in day_choices:
        for room in room_choices:
            for time in time_choices:
                obj = ShiftTemplate.objects.create(
                    day=day,
                    time=time,
                    room=room,
                    is_next_year=False,
                )

                empty_classes = ShiftTemplateLessonRelation.objects.create()
                obj.lessons = empty_classes
                obj.save()

    # 次年度テンプレートの作成
    for day in day_choices:
        for room in room_choices:
            for time in time_choices:
                obj = ShiftTemplate.objects.create(
                    day=day,
                    time=time,
                    room=room,
                    is_next_year=True,
                )

                empty_classes = ShiftTemplateLessonRelation.objects.create()
                obj.lessons = empty_classes
                obj.save()

def create_teacher(username, last_name, first_name):
    teacher = CustomUser.objects.create(
        username=username,
        last_name=last_name,
        first_name=first_name,
        is_teacher=True,
        is_staff=True,
        is_superuser=True
    )
    teacher.set_password('detteiu')
    teacher.save()
    
    TeacherProfile.objects.create(user=teacher)

def create_parent_and_student(parent_last_name, parent_first_name, parent_username, student_last_name, student_first_name, birth_date, school):
    try:
        parent = CustomUser.objects.get(last_name=parent_last_name, first_name=parent_first_name)
        parent_profile = ParentProfile.objects.get(user=parent)

    except CustomUser.DoesNotExist:
        parent = CustomUser.objects.create(last_name=parent_last_name, first_name=parent_first_name, username=parent_username, is_parent=True, is_staff=True, is_superuser=True)
        parent.set_password('detteiu')
        parent.save()
        parent_profile = ParentProfile.objects.create(user=parent)

    student = Student.objects.create(last_name=student_last_name, first_name=student_first_name, birth_date=birth_date, school=school)
    student.update_grade()
    parent_profile.student.add(student)
    parent_profile.current_student = student
    parent_profile.save()

    semester_choices = [semester[0] for semester in SEMESTER_CHOICES]
    subject_choices = [subject[0] for subject in REPORT_SUBJECT_CHOICES]

    for semester in semester_choices:
        for subject in subject_choices:
            ReportGrade.objects.create(
                student=student,
                semester=semester,
                subject=subject,
            )

    category_choices = [category[0] for category in CATEGORY_CHOICES]
    program_choices = [program[0] for program in PROGRAM_CHOICES]
    count_choices = [count[0] for count in COUNT_CHOICES]

    for category in category_choices:
        for program in program_choices:
            for count in count_choices:
                TestResult.objects.create(
                    student=student,
                    category=category,
                    program=program,
                    count=count,
                )


class Command(BaseCommand):
    help = 'モデルを自動で作成します'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write("テストユーザーを作成中...")

            create_owner('contact@proselll.com', '塾長', '太郎')

            admin = CustomUser.objects.create(
                username='admin',
                is_owner=False,
                is_staff=True,
                is_superuser=True,
            )
            admin.set_password(os.environ.get('ADMIN_PASSWORD'))
            admin.save()

            # 全て完了した時
            self.stdout.write(self.style.SUCCESS('全てのユーザーの作成が終了しました'))
