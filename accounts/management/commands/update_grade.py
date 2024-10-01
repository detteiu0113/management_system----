from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from shift.models import ShiftTemplate, ShiftTemplateLessonRelation
from regular_lesson.models import RegularLessonAdmin
from teacher_shift.models import FixedShift
from students.models import Student
from vocabulary_test.models import TestResult
from utils.choices import DAY_CHOICES, ROOM_CHOICES, TIME_CHOICES
from utils.helpers import get_fiscal_year_boundaries, generate_regular_lessons, generate_teacher_shifts, get_today

class Command(BaseCommand):
    def handle(self, *args, **options):
        with transaction.atomic():
            # 昨年度のTemplateを削除
            ShiftTemplate.objects.filter(is_next_year=False).delete()

            # 新年度のtemplateに切り替え
            next_templates = ShiftTemplate.objects.filter(is_next_year=True)
            for template in next_templates:
                template.is_next_year = False
                template.save()

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
                            is_next_year=True,
                        )

                        empty_classes = ShiftTemplateLessonRelation.objects.create()
                        obj.lessons = empty_classes
                        obj.save()

            today = get_today()
            today_of_last_year = today - relativedelta(years=1)
            start_date, end_date = get_fiscal_year_boundaries(today)
            start_date_of_last_fiscal_year, end_date_of_last_fiscal_year = get_fiscal_year_boundaries(today_of_last_year)

            # 昨年の固定授業をフィルタリング
            regular_lesson_admins = RegularLessonAdmin.objects.filter(end_date=end_date_of_last_fiscal_year)
            for regular_lesson in regular_lesson_admins:

                # 昨年度に切り替えが完了しているものの処理
                if regular_lesson.is_upgraded:
                    regular_lesson.is_upgraded = False
                    regular_lesson.save()

            fixed_shifts = FixedShift.objects.filter(end_date=end_date_of_last_fiscal_year)
            for fixed_shift in fixed_shifts:

                # 昨年切り替えが完了しているものの処理
                if fixed_shift.is_upgraded:
                    fixed_shift.is_upgraded = False
                    fixed_shift.save()

            # 全生徒の学年を更新する
            students = Student.objects.all()

            for student in students:

                # 退塾予定の生徒は退塾
                if student.is_planning_to_withdraw:
                    student.is_planning_to_withdraw = False
                    student.is_withdrawn = True

                student.update_grade()
                student.save()

            # 英単語テストの結果をリセット
            TestResult.objects.all().update(date=None, score=None, fullscore=None)

            print(f'{date.today()}の年度切り替えが完了')