from datetime import timedelta
import datetime

from django.db.models import Case, When

from accounts.models import CustomUser
from shift.models import ShiftTemplate, Shift, ShiftLessonRelation
from regular_lesson.models import Lesson
from special_lesson.models import SpecialLesson, SpecialLessonTeacherRequest
from teacher_shift.models import TeacherShift
from year_schedule.models import Event
from utils.choices import ROOM_CHOICES, TIME_CHOICES, SPECIAL_TIME_CHOICES

def get_today():
    # 大体の時刻設定がここで可能(JSを除く)
    return datetime.date.today()


# RegularLessonAdminに伴うLessonの作成及び、ShiftTemplateへの登録
def generate_regular_lessons(regular_lesson_admin, day, time, start_date, end_date, is_next_year=False): # 来年度の場合のみTrue
    clousure_dates = [obj.date for obj in Event.objects.filter(date__gte=start_date, date__lte=end_date, is_closure=True)]

    # gradeをLessonに反映
    grade = regular_lesson_admin.grade

    current_date = start_date
    # 曜日が一致した場合はその曜日しか作成しない
    skip = False

    while current_date <= end_date:
        # 休校日の場合は授業を作成しない
        if not current_date in clousure_dates:
            # 曜日が一致する場合のみLessonインスタンスを作成
            if current_date.weekday() == int(day) - 1:  # 月曜日が1に対応するため、dayから1を引きます
                Lesson.objects.create(
                    regular=regular_lesson_admin,
                    student=regular_lesson_admin.student,
                    grade=grade,
                    subject=regular_lesson_admin.subject,
                    date=current_date,
                    time=time,
                    is_regular=True,
                )
                # 7日進めてforloopを短縮
                skip = True
                current_date += timedelta(days=7)
            else:
                # 曜日が合わない場合は一日ずつ進める
                current_date += timedelta(days=1)
        else:
            if skip:
                current_date += timedelta(days=7)
            else:
                current_date += timedelta(days=1)

    # ShiftTemplateに登録する処理
    room_choices = [room[0] for room in ROOM_CHOICES]
    regular_lesson_time_table_added = False
    for room in room_choices:
        obj = ShiftTemplate.objects.get(
            day=day,
            time=time,
            room=room,
            is_next_year=is_next_year
        )
        if not regular_lesson_time_table_added:
            for i in range(1, 5):
                template_lesson = getattr(obj.lessons, f"template_lesson{i}")
                if template_lesson is None:
                    setattr(obj.lessons, f"template_lesson{i}", regular_lesson_admin)
                    obj.lessons.save()
                    regular_lesson_time_table_added = True
                    break
        else:
            break

# FixedShiftに伴うTeacherShiftの作成及び、ShiftTemplateへの登録
def generate_teacher_shifts(fixed_shift, day, time, start_date, end_date, is_next_year=False):
    clousure_dates = [obj.date for obj in Event.objects.filter(date__gte=start_date, date__lte=end_date, is_closure=True)]

    current_date = start_date
    # 曜日が一致した場合はその曜日しか作成しない
    skip = False

    while current_date <= end_date:
        # 休校日の場合は授業を作成しない
        if not current_date in clousure_dates:
            # 曜日が一致する場合のみLessonインスタンスを作成
            if current_date.weekday() == int(day) - 1:  # 月曜日が1に対応するため、dayから1を引きます
                TeacherShift.objects.create(
                    teacher=fixed_shift.teacher,
                    fixed_shift=fixed_shift,
                    date=current_date,
                    time=time,
                    is_fixed=True,
                )
                # 7日進めてforloopを短縮
                skip = True
                current_date += timedelta(days=7)
            else:
                # 曜日が合わない場合は一日ずつ進める
                current_date += timedelta(days=1)
        else:
            if skip:
                current_date += timedelta(days=7)
            else:
                current_date += timedelta(days=1)
    
    # ShiftTemplateを登録するための処理
    room_choices = [room[0] for room in ROOM_CHOICES]
    teacher_time_table_added = False
    for room in room_choices:
        obj = ShiftTemplate.objects.get(
            day=day,
            time=time,
            room=room,
            is_next_year=is_next_year,
        )
        if not teacher_time_table_added:
            template_teacher = obj.fixed_shift
            if template_teacher is None:
                obj.fixed_shift = fixed_shift
                obj.save()
                teacher_time_table_added = True
                break
        else:
            break

# 日付からその日のシフトオブジェクトを作成する(休校日の判別は含まない)(シフトが存在するかどうかの判別は含む)
def generate_shifts(date):

    # 月曜日を1として曜日を取得
    day = date.weekday() + 1
    
    # 年度末を取得する
    _, end_date = get_fiscal_year_boundaries(date)

    # シフトが存在しない場合は作成
    if not Shift.objects.filter(date=date).exists():

        # 年度末より前の場合は今年のテンプレート、それ以降の場合は来年度のテンプレートを使用
        if date <= end_date:
            shift_templates = ShiftTemplate.objects.filter(day=day ,is_next_year=False)
        else:
            shift_templates = ShiftTemplate.objects.filter(day=day, is_next_year=True)

        # シフトテンプレートからシフトを作成
        for shift_template in shift_templates:
            fixed_shift = shift_template.fixed_shift
            room = shift_template.room
            time = shift_template.time

            # 固定シフトを取得
            try:
                teacher_shift = TeacherShift.objects.get(
                    fixed_shift=fixed_shift,
                    date=date,
                    is_fixed=True,
                )

            except TeacherShift.DoesNotExist:
                teacher_shift = None
            
            # 通常授業を取得
            lessons = []
            for i in range(1, 5):
                regulr_lesson_admin = getattr(shift_template.lessons, f"template_lesson{i}")
                try:
                    lesson = Lesson.objects.get(
                        regular=regulr_lesson_admin,
                        is_regular=True,
                        date=date,
                        is_rescheduled=False,
                    )
                except Lesson.DoesNotExist:
                    lesson = None
                lessons.append(lesson)

            # それを元にShiftオブジェクトを作成
            obj = Shift.objects.create(
                date=date,
                time=time,
                room=room,
            )

            # 中間モデルを作成
            shift_lesson_relation = ShiftLessonRelation.objects.create(
                lesson1=lessons[0],
                lesson2=lessons[1],
                lesson3=lessons[2],
                lesson4=lessons[3],
            )

            obj.lessons = shift_lesson_relation
            obj.teacher_shift=teacher_shift
            obj.lessons=shift_lesson_relation
            obj.save()

    # 削除した時に復元
    if Lesson.objects.filter(date=date, is_regular=False).exists():
        lessons = Lesson.objects.filter(date=date, is_regular=False)
        for lesson in lessons:
            unregisterd_lesson = lesson
            time = lesson.time
            room_choices = [room[0] for room in ROOM_CHOICES]
            lesson_added = False
            for room in room_choices:
                obj = Shift.objects.get(
                    date=date,
                    time=time,
                    room=room,
                )
                if not lesson_added:
                    for i in range(1, 5):
                        lesson = getattr(obj.lessons, f"lesson{i}")
                        if lesson is None:
                            setattr(obj.lessons, f"lesson{i}", unregisterd_lesson)
                            obj.lessons.save()
                            lesson_added = True
                            break
                else:
                    break
    # 削除した時に復元    
    if TeacherShift.objects.filter(date=date, is_fixed=False).exists():
        teacher_shifts = TeacherShift.objects.filter(date=date, is_fixed=False)
        for teacher_shift in teacher_shifts:
            unregisterd_teacher = teacher_shift
            time = unregisterd_teacher.time
            room_choices = [room[0] for room in ROOM_CHOICES]
            teacher_added = False
            for room in room_choices:
                obj = Shift.objects.get(
                    date=date,
                    time=time,
                    room=room,
                )
                if not teacher_added:
                    for i in range(1, 5):
                        if obj.teacher_shift is None:
                            obj.teacher_shift = unregisterd_teacher
                            obj.save()
                            teacher_added = True
                            break
                else:
                    break

    # 講習授業の対象日の場合
    if SpecialLesson.objects.filter(start_date__lte=date, end_date__gte=date).exists():
        special_lesson = SpecialLesson.objects.get(start_date__lte=date, end_date__gte=date)
        teachers = CustomUser.objects.filter(is_teacher=True)

        # 授業の拡張が有効でそれらのまだ授業が存在していない場合に授業を作成
        if special_lesson.is_extend and len(Shift.objects.filter(date=date)) == len(ROOM_CHOICES) * len(TIME_CHOICES):
            room_choices = [room[0] for room in ROOM_CHOICES]
            special_time_choices = [time[0] for time in SPECIAL_TIME_CHOICES]

            for room in room_choices:
                for time in special_time_choices:
                    obj = Shift.objects.create(
                        date=date,
                        room=room,
                        time=time,
                    )
                    shift_lesson_relation = ShiftLessonRelation.objects.create()
                    obj.lessons = shift_lesson_relation
                    obj.save()

        for teacher in teachers:

            # 講師の希望オブジェクトが存在しない場合に新規作成(SpecialLessonモデルにのみ依存するため、存在の確認のみで良い)
            if not SpecialLessonTeacherRequest.objects.filter(teacher=teacher, date=date, special_lesson=special_lesson).exists():

                # 拡張の場合
                if special_lesson.is_extend:
                    time_choices = [time[0] for time in TIME_CHOICES] + [time[0] for time in SPECIAL_TIME_CHOICES]
                else:
                    time_choices = [time[0] for time in TIME_CHOICES]

                for time in time_choices:
                    SpecialLessonTeacherRequest.objects.create(
                        teacher=teacher,
                        special_lesson=special_lesson,
                        date=date,
                        time=time
                    )

# Mixinからheplaer関数に移動
def get_fiscal_year_boundaries(input_date):
    year = input_date.year

    # Determine fiscal year start and end dates
    fiscal_year_start = datetime.date(year, 3, 1)
    if input_date < fiscal_year_start:
        fiscal_year_start = datetime.date(year - 1, 3, 1)
    fiscal_year_end = datetime.date(year, 2, 28 if year % 4 != 0 or (year % 100 == 0 and year % 400 != 0) else 29)
    if input_date >= fiscal_year_start:
        fiscal_year_end = datetime.date(year + 1, 2, 28 if (year + 1) % 4 != 0 or ((year + 1) % 100 == 0 and (year + 1) % 400 != 0) else 29)

    return fiscal_year_start, fiscal_year_end

# 4月で年度切り替え用の関数
def get_fiscal_year_boundaries_april(input_date):
    year = input_date.year

    # Determine fiscal year start and end dates
    fiscal_year_start = datetime.date(year, 4, 1)
    if input_date < fiscal_year_start:
        fiscal_year_start = datetime.date(year - 1, 4, 1)
    fiscal_year_end = datetime.date(year, 3, 31)  # March 31st is always the end, no need for leap year calculation

    if input_date >= fiscal_year_start:
        fiscal_year_end = datetime.date(year + 1, 3, 31)

    return fiscal_year_start, fiscal_year_end

def get_special_ordering():
    custom_order = [time[0] for time in SPECIAL_TIME_CHOICES] + [time[0] for time in TIME_CHOICES]
    return Case(*[When(time=t, then=pos) for pos, t in enumerate(custom_order)])