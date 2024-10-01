from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from shift.models import ShiftTemplate, ShiftTemplateLessonRelation
from regular_lesson.models import RegularLessonAdmin
from teacher_shift.models import FixedShift
from students.models import Student
from vocabulary_test.models import TestResult
from utils.choices import DAY_CHOICES, ROOM_CHOICES, TIME_CHOICES
from utils.helpers import get_fiscal_year_boundaries, generate_regular_lessons, generate_teacher_shifts

from celery import shared_task

@shared_task
def update_grade():
    # 昨年度のTemplateを削除
    ShiftTemplate.objects.filter(is_next_year=False).delete()

    # 新年度のtemplateに切り替え
    next_templates = ShiftTemplate.objects.filter(is_next_year=True)
    for template in next_templates:
        template.is_next_year = False
    ShiftTemplate.objects.bulk_update(next_templates, ['is_next_year'])

    # 来年度シフトテンプレートの作成
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

    today = date.today()
    today_of_last_year = today - relativedelta(years=1)
    start_date, end_date = get_fiscal_year_boundaries(today)
    start_date_of_last_fiscal_year, end_date_of_last_fiscal_year = get_fiscal_year_boundaries(today_of_last_year)

    # 固定授業の切り替え
    regular_lesson_admins = RegularLessonAdmin.objects.filter(end_date=end_date_of_last_fiscal_year)
    for regular_lesson in regular_lesson_admins:

        # 昨年切り替えが完了しているものの処理
        if regular_lesson.is_upgraded:
            regular_lesson.is_upgraded = False
            regular_lesson.save()

        # 昨年切り替えていないものは全て継続で処理
        else:
            student = regular_lesson.student
            grade = regular_lesson.grade
            subject = regular_lesson.subject
            day = regular_lesson.day
            time = regular_lesson.time

            # 過年度生は13のまま処理する
            if grade == 13:
                new_grade = 13
            else:
                new_grade = grade + 1

            regular_lesson_admin =  RegularLessonAdmin.objects.create(
                student=student,
                grade=new_grade,
                subject=subject,
                day=day,
                time=time,
                start_date=start_date,
                end_date=end_date
            )

            generate_regular_lessons(regular_lesson_admin, day, time, start_date, end_date, is_next_year=False)

    fixed_shifts = FixedShift.objects.filter(end_date=end_date_of_last_fiscal_year)
    for fixed_shift in fixed_shifts:

        if fixed_shift.is_upgraded:
            fixed_shift.is_upgraded = False
            fixed_shift.save()

        else:
            teacher = fixed_shift.teacher
            day = fixed_shift.day
            time = fixed_shift.time

            fixed_shift = FixedShift.objects.create(
                teacher=teacher,
                day=day,
                time=time,
                start_date=start_date,
                end_date=end_date
            )

            generate_teacher_shifts(fixed_shift, day, time, start_date, end_date, is_next_year=True)

    # 全生徒の学年を更新する
    students = Student.objects.all()

    for student in students:

        # 退塾予定の生徒は退塾
        if student.is_planning_to_withdraw:
            student.is_planning_to_withdraw = False
            student.is_withdrawn = True

        student.update_grade()
        student.is_upgraded = False
        student.save()

    # 英単語テストの結果をリセット
    TestResult.objects.all().update(date=None, score=None, fullscore=None)

    return print('Success')