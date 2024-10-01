from datetime import datetime, timedelta
import datetime as datetime_module
import json

from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.views.generic import TemplateView, ListView, View
from django.views.generic.base import RedirectView
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, F
from django.contrib import messages
from django.urls import reverse_lazy

from .models import ShiftTemplate, ShiftTemplateLessonRelation, Shift, ShiftLessonRelation
from .forms import TeacherAddForm, TransferLessonForm
from regular_lesson.models import Lesson, RegularLessonAdmin
from teacher_shift.models import TeacherShift, FixedShift, TemporalyShift
from special_lesson.models import SpecialLesson, SpecialLessonTeacherRequest, SpecialLessonStudentRequest, SpecialLessonAdmin
from year_schedule.models import Event
from accounts.decorators import user_type_required
from utils.choices import ROOM_CHOICES, TIME_CHOICES, SPECIAL_TIME_CHOICES
from utils.mixins import FiscalYearMixin
from utils.helpers import get_today, generate_shifts, get_special_ordering, get_fiscal_year_boundaries

@method_decorator(user_type_required(), name='dispatch')
class ShiftSelectView(FiscalYearMixin, TemplateView):
    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else 'teacher'
        return [f'{user_type}/shift_select.html']


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = get_today()
        start_date, end_date = get_fiscal_year_boundaries(today)
        shifts = Shift.objects.filter(time=1, room=1)
        
        iso_weeks = []
        for shift in shifts:
            iso_year, iso_week, _ = shift.date.isocalendar()
            iso_weeks.append({'year': iso_year, 'week': iso_week})

        unique_iso_weeks = []
        added_iso_weeks = set()
        for iso_week in iso_weeks:
            if (iso_week['year'], iso_week['week']) not in added_iso_weeks:
                unique_iso_weeks.append(iso_week)
                added_iso_weeks.add((iso_week['year'], iso_week['week']))

        week_list = []
        for year_week in sorted(unique_iso_weeks, key=lambda x: (x['year'], x['week'])):
            year = year_week['year']
            week = year_week['week']
            start_of_week = datetime.fromisocalendar(year, week, 1)
            week_dates = [start_of_week + timedelta(days=i) for i in range(5)]
            monday = week_dates[0]
            friday = week_dates[-1]

            # 年と週の情報と日付を日本語に変換してリストに追加
            week_list.append({
                'year': year,
                'week': week,
                'monday': monday.strftime('%Y年%m月%d日'),
                'friday': friday.strftime('%m月%d日')
            })

        context['week_list'] = week_list
        return context

@method_decorator(user_type_required(), name='dispatch')
class ShiftTemplateView(ListView):
    model = ShiftTemplate
    context_object_name = 'shifts'
    template_name = 'owner/shift_template.html'
    paginate_by = 30

    def get_queryset(self):
        return ShiftTemplate.objects.filter(is_next_year=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_choices'] = [time[1] for time in TIME_CHOICES]
        return context

@method_decorator(user_type_required(), name='dispatch')
class ShiftTemplateUpdateView(View):
    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)
        
        for item in json_data['lessons']:
            relation_id, relation_number = item['id'].split('-')
            lesson_id = item['lessonId']

            shift_relation_obj = ShiftTemplateLessonRelation.objects.prefetch_related().get(id=relation_id)
            new_class_obj = RegularLessonAdmin.objects.get(id=lesson_id) if lesson_id else None

            template_lesson_mapping = {
                '1': 'template_lesson1',
                '2': 'template_lesson2',
                '3': 'template_lesson3',
                '4': 'template_lesson4'
            }

            template_lesson_field = template_lesson_mapping.get(relation_number)

            if template_lesson_field:
                setattr(shift_relation_obj, template_lesson_field, new_class_obj)
                shift_relation_obj.save()

        for item in json_data['teachers']:
            shift_id = item['id']
            teacher_id = item['teacherId']

            shift_obj = ShiftTemplate.objects.get(id=shift_id)
            new_teacher_obj = FixedShift.objects.get(id=teacher_id) if teacher_id else None
            
            shift_obj.fixed_shift = new_teacher_obj
            shift_obj.save()

        messages.success(self.request, "保存できました")
        return JsonResponse({'success': True})
    
    
@method_decorator(user_type_required(), name='dispatch')
class ShiftDetailDisplayView(ListView):
    model = Shift
    context_object_name = 'shifts'

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else 'teacher'
        return [f'{user_type}/shift_display.html']

    def get_queryset(self):
        year = self.kwargs['year']
        week = self.kwargs['week']
        day = self.kwargs['day']
        # グローバル変数として明記
        global_date = datetime.fromisocalendar(year, week, day).date()
        return Shift.objects.filter(date=global_date).order_by('room', get_special_ordering())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs['year']
        week = self.kwargs['week']
        day = self.kwargs['day']
        global_date = datetime.fromisocalendar(year, week, day).date()
        context['year'] = year
        context['week'] = week
        context['day'] = day
        context['date'] = global_date

        # ページネーションの作成
        start_of_week = datetime.fromisocalendar(year, week, 1).date()
        week_dates = [start_of_week + timedelta(days=i) for i in range(5)]
        japanese_weekdays = {
            0: '月',
            1: '火',
            2: '水',
            3: '木',
            4: '金',
            5: '土',
            6: '日'
        }
        context['dates'] = [date.strftime('%m/%d(%a)').replace(date.strftime('%a'), japanese_weekdays[date.weekday()]) for date in week_dates]

        try:
            special_lesson = SpecialLesson.objects.get(start_date__lte=global_date, end_date__gte=global_date)
            is_extend = special_lesson.is_extend
        except SpecialLesson.DoesNotExist:
            special_lesson = None
            is_extend = False

        # 拡張が有効な場合は時間割を拡張
        if is_extend:
            context['time_choices'] =  [time[1] for time in SPECIAL_TIME_CHOICES] + [time[1] for time in TIME_CHOICES]
        else:
            context['time_choices'] = [time[1] for time in TIME_CHOICES]

        context['is_extend'] = is_extend

        return context
 
@method_decorator(user_type_required(), name='dispatch')
class ShiftDetailView(FiscalYearMixin, ListView):
    model = Shift
    context_object_name = 'shifts'
    template_name = 'owner/shift_detail.html'

    def get_queryset(self):
        year = self.kwargs['year']
        week = self.kwargs['week']
        day = self.kwargs['day']
        # グローバル変数として明記
        global_date = datetime.fromisocalendar(year, week, day).date()

        start_of_week = datetime.fromisocalendar(year, week, 1).date()
        week_dates = [start_of_week + timedelta(days=i) for i in range(5)]

        clousure_dates = [obj.date for obj in Event.objects.filter(date__gte=week_dates[0], date__lte=week_dates[-1], is_closure=True)]
        boolean_list = []

        def check_shift_existance(date):
            # 休校日かどうか
            if date in clousure_dates:
                return True
            else:
                # シフトが存在するか
                if Shift.objects.filter(date=date).exists():
                    return True
                else:
                    return False

        for date in week_dates:
            boolean_list.append(check_shift_existance(date))

        # シフトが存在する場合その日のみのシフトを返して終了
        if all(boolean_list):
            return Shift.objects.filter(date=global_date).order_by('room', get_special_ordering())

        # シフトが存在しない場合にまとめて作成する
        else:
            for index, date in enumerate(week_dates, start=0):

                # シフトが存在しない日付のにmみシフトを作成
                if not boolean_list[index]:
                    generate_shifts(date)

            return Shift.objects.filter(date=global_date).order_by('room', get_special_ordering())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs['year']
        week = self.kwargs['week']
        day = self.kwargs['day']
        global_date = datetime.fromisocalendar(year, week, day).date()
        context['year'] = year
        context['week'] = week
        context['day'] = day
        context['date'] = global_date

        # ページネーションの作成
        start_of_week = datetime.fromisocalendar(year, week, 1).date()
        week_dates = [start_of_week + timedelta(days=i) for i in range(5)]
        japanese_weekdays = {
            0: '月',
            1: '火',
            2: '水',
            3: '木',
            4: '金',
            5: '土',
            6: '日'
        }
        context['dates'] = [date.strftime('%m/%d(%a)').replace(date.strftime('%a'), japanese_weekdays[date.weekday()]) for date in week_dates]

        try:
            special_lesson = SpecialLesson.objects.get(start_date__lte=global_date, end_date__gte=global_date)
            is_extend = special_lesson.is_extend
        except SpecialLesson.DoesNotExist:
            special_lesson = None
            is_extend = False

        # 拡張が有効な場合は時間割を拡張
        if is_extend:
            context['time_choices'] =  [time[1] for time in SPECIAL_TIME_CHOICES] + [time[1] for time in TIME_CHOICES]
            times = [time[0] for time in SPECIAL_TIME_CHOICES] + [time[0] for time in TIME_CHOICES]
        else:
            context['time_choices'] = [time[1] for time in TIME_CHOICES]
            times = [time[0] for time in TIME_CHOICES]

        transfer_lesson_form = TransferLessonForm()
        transfer_lesson_form.fields['lesson'].queryset = Lesson.objects.filter(is_absence=True, is_unauthorized_absence=False, is_rescheduled=False)
        json_data = {}

        for time in times:
            json_data[time] = {}
            teacher_requests = SpecialLessonTeacherRequest.objects.filter(special_lesson=special_lesson, date=global_date, time=time, is_available=True)
            teachers = [request.teacher.id for request in teacher_requests]
            json_data[time]['teachers'] = teachers
            student_requests = SpecialLessonStudentRequest.objects.filter(special_lesson=special_lesson, date=global_date, time=time, is_available=True)
            students = [request.student.id for request in student_requests]
            json_data[time]['students'] = students

        # 特別講習がある場合は希望調査の結果を反映
        if special_lesson:
            special_lesson_admins = SpecialLessonAdmin.objects.filter(
                special_lesson=special_lesson
            ).annotate(
                lesson_count=Count('lesson')  # 'lesson'は関連するLessonモデルの関連名
            ).filter(
                lesson_count__lt=F('periods')  # 'periods'はSpecialLessonAdminのフィールド
            )
            transfer_lesson_form.fields['special_lesson'].queryset = special_lesson_admins
            transfer_lesson_form.fields['special_lesson_others'].queryset = special_lesson_admins

        context['json_data'] = json_data
        context['special_lesson'] = special_lesson
        context['transfer_lesson_form'] = transfer_lesson_form
        context['teacher_add_form'] = TeacherAddForm()
        return context
    
@method_decorator(user_type_required(), name='dispatch')
class ShiftDetailUpdateView(View):
    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)
        
        for item in json_data['lessons']:
            # lessonの処理
            relation_id, relation_number = item['id'].split('-')
            lesson_id = item['lessonId']

            shift_relation_obj = ShiftLessonRelation.objects.prefetch_related().get(id=relation_id)
            new_class_obj = Lesson.objects.get(id=lesson_id) if lesson_id else None

            lesson_mapping = {
                '1': 'lesson1',
                '2': 'lesson2',
                '3': 'lesson3',
                '4': 'lesson4'
            }

            lesson_field = lesson_mapping.get(relation_number)

            if lesson_field:
                setattr(shift_relation_obj, lesson_field, new_class_obj)
                shift_relation_obj.save()

        for item in json_data['teachers']:
            # teacherの処理
            shift_id = item['id']
            teacher_id = item['teacherId']

            shift_obj = Shift.objects.prefetch_related().get(id=shift_id)
            new_teacher_obj = TeacherShift.objects.get(id=teacher_id) if teacher_id else None

            shift_obj.teacher_shift = new_teacher_obj
            shift_obj.save()
        messages.success(request, "編集できました")

        return JsonResponse({'success': True})
    
# リロードは全てのシフトが対象
@method_decorator(user_type_required(), name='dispatch')
class ShiftDetailReloadView(RedirectView):
    def get_week_dates(self, year, week):
        start_of_week = datetime.fromisocalendar(year, week, 1)
        week_dates = [start_of_week + timedelta(days=i) for i in range(5)]
        formatted_dates = [date.strftime("%Y-%m-%d") for date in week_dates]
        return formatted_dates

    def get(self, request, *args, **kwargs):
        year = self.kwargs['year']
        week = self.kwargs['week']
        dates = self.get_week_dates(year, week)

        # 新たに新規作成された授業を追加する
        lesson_instances = Lesson.objects.filter(date__in=dates, is_absence=False)
        for lesson_instance in lesson_instances:
            related_shift_lesson_relations = lesson_instance.lesson1.all() | \
                                            lesson_instance.lesson2.all() | \
                                            lesson_instance.lesson3.all() | \
                                            lesson_instance.lesson4.all()
            if not related_shift_lesson_relations.exists():
                unregisterd_lesson = lesson_instance
                date = unregisterd_lesson.date
                time = unregisterd_lesson.time
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
        
        # 新たに新規作成された講師シフトを追加
        teacher_instances = TeacherShift.objects.filter(date__in=dates)
        for teacher_instance in teacher_instances:
            try:
                related_teacher_relations = teacher_instance.teacher_shift
            except ObjectDoesNotExist:
                # 関連が存在しない場合の処理
                related_teacher_relations = None
                
            if not related_teacher_relations:
                unregisterd_teacher = teacher_instance
                date = unregisterd_teacher.date
                time = unregisterd_teacher.fixed_shift.time
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
        
        return super().get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        messages.success(self.request, "更新しました")
        referer = self.request.META.get('HTTP_REFERER')
        if referer:
            return referer
        else:
            return HttpResponseBadRequest('Referer header not found')
    
@method_decorator(user_type_required(), name='dispatch')
class ShiftLessonCreateView(FiscalYearMixin, View):
    def post(self, request, *args, **kwargs):
        form = TransferLessonForm(self.request.POST)
        print(form.errors)
        if form.is_valid():
            # 共通のデータ
            date = form.cleaned_data['date']
            room = form.cleaned_data['room']
            time = form.cleaned_data['time']
            student = form.cleaned_data['student']
            subject = form.cleaned_data['subject']
            lesson = form.cleaned_data['lesson']
            special_lesson = form.cleaned_data['special_lesson']
            special_lesson_others = form.cleaned_data['special_lesson_others']

            # 臨時授業の追加
            if student and subject:
                student = form.cleaned_data['student']
                subject = form.cleaned_data['subject']
                grade = student.grade
                lesson = Lesson.objects.create(
                    student=student,
                    grade=grade,
                    date=date,
                    time=time,
                    subject=subject,
                    is_temporaly=True,
                )

            # 授業の振替
            elif lesson:
                lesson.rescheduled_date = date
                lesson.room = room
                lesson.rescheduled_time = time
                # 年度を超えて振り替えた場合に学年を更新
                lesson.grade = lesson.student.grade
                lesson.is_absence = False
                lesson.is_rescheduled = True
                lesson.save()
            
            # 講習授業の追加
            elif special_lesson or special_lesson_others:
                if special_lesson:
                    special_lesson_admin = special_lesson
                else:
                    special_lesson_admin = special_lesson_others
                today = get_today()
                _, end_date = self.get_fiscal_year_boundaries(today)

                if date <= end_date:
                    grade = special_lesson_admin.grade
                # 来年度の講習を作成した際に過年度生でなければ学年を一つ進める
                else:
                    if special_lesson_admin.grade == 13:
                        grade = 13
                    else:
                        grade = special_lesson_admin.grade + 1
                        
                lesson = Lesson.objects.create(
                    special=special_lesson_admin,
                    student=special_lesson_admin.student,
                    grade=grade,
                    subject=special_lesson_admin.subject,
                    date=date,
                    time=time,
                    is_regular=False,
                )

            else:
                messages.error(request, '追加する授業を選択してください。')
                referer = request.META.get('HTTP_REFERER')
                if referer:
                    return HttpResponseRedirect(referer)
                else:
                    return HttpResponseBadRequest('Referer header not found')

            unregisterd_lesson = lesson
            obj = Shift.objects.get(date=date, room=room, time=time)
            for i in range(1, 5):
                lesson = getattr(obj.lessons, f"lesson{i}")
                if lesson is None:
                    setattr(obj.lessons, f"lesson{i}", unregisterd_lesson)
                    obj.lessons.save()
                    break

        referer = request.META.get('HTTP_REFERER')
        if referer:
            return HttpResponseRedirect(referer)
        else:
            return HttpResponseBadRequest('Referer header not found')
    
# RemoveStudentView
@method_decorator(user_type_required(), name='dispatch')
class ShiftLessonDeleteView(RedirectView):
    def get(self, request, *args, **kwargs):

        # 授業の欠席
        lesson_pk = self.kwargs['lesson_pk']
        relation_num = self.kwargs['relation_num']
        unauthorized_absence = self.kwargs['unauthorized_absence']
        lesson_instance = Lesson.objects.get(pk=lesson_pk)

        # 特別授業の振替は削除を持って実施(ただし無断欠席の場合は実施なし)
        if lesson_instance.is_regular == False and lesson_instance.is_temporaly == False and unauthorized_absence == False:
            lesson_instance.delete()
            return super().get(request, *args, **kwargs)
        
        # それ以外の場合は欠席にする(通常授業の欠席は振替)(臨時授業も同様に処理)
        else:
            lesson_instance.is_absence = True

            # 振替の振替に対応
            lesson_instance.is_rescheduled = False
        
        # 無断欠席の場合は振替を実施しない
        if unauthorized_absence == 1:
            lesson_instance.is_unauthorized_absence = True

        lesson_instance.save()
        related_shift_lesson_relations = getattr(lesson_instance, f'lesson{relation_num}')
        update_data = {f'lesson{relation_num}': None}
        related_shift_lesson_relations.update(**update_data)

        return super().get(request, *args, **kwargs)
    
    def get_redirect_url(self, *args, **kwargs):
        referer = self.request.META.get('HTTP_REFERER')
        if referer:
            return referer
        else:
            return HttpResponseBadRequest('Referer header not found')

# AddTeacherView
@method_decorator(user_type_required(), name='dispatch')
class ShiftTeacherShiftCreateView(View):
    def post(self, request, *args, **kwargs):
        form = TeacherAddForm(self.request.POST)

        if form.is_valid():
            # 固定シフト以外の講師の追加
            date = form.cleaned_data['date']
            room = form.cleaned_data['room']
            time = form.cleaned_data['time']
            teacher = form.cleaned_data['teacher'] or form.cleaned_data['special_teacher']
            temporaly_shift = TemporalyShift.objects.create(teacher=teacher, date=date, time=time)
            teacher_shift = TeacherShift.objects.create(teacher=teacher, temporaly_shift=temporaly_shift, date=date, time=time, is_fixed=False)
            shift = Shift.objects.get(date=date, time=time, room=room)
            shift.teacher_shift = teacher_shift
            shift.save()
        
        else:
            messages.error(request, '追加する講師を選択してください。')

        referer = request.META.get('HTTP_REFERER')
        if referer:
            return HttpResponseRedirect(referer)
        else:
            return HttpResponseBadRequest('Referer header not found')

# RemoveTeacherView
@method_decorator(user_type_required(), name='dispatch')
class ShiftTeacherShiftDeleteView(RedirectView):
    def get(self, request, *args, **kwargs):

        # 講師シフトの削除
        teacher_shift_pk = self.kwargs['teacher_shift_pk']
        teacher_shift = TeacherShift.objects.get(pk=teacher_shift_pk)
        temporaly_shift = teacher_shift.temporaly_shift
        if temporaly_shift:
            temporaly_shift.delete()
        teacher_shift.delete()
        return super().get(request, *args, **kwargs)
    
    def get_redirect_url(self, *args, **kwargs):
        referer = self.request.META.get('HTTP_REFERER')
        if referer:
            return referer
        else:
            return HttpResponseBadRequest('Referer header not found')
        
class ShiftDeleteView(View):

    def get_week_dates(self, year, week):
        start_of_week = datetime.fromisocalendar(year, week, 1)
        week_dates = [start_of_week + timedelta(days=i) for i in range(5)]
        formatted_dates = [date.strftime("%Y-%m-%d") for date in week_dates]
        return formatted_dates

    def post(self, request, *args, **kwargs):
        year = self.kwargs['year']
        week = self.kwargs['week']
        dates = self.get_week_dates(year, week)
        Shift.objects.filter(date__in=dates).delete()
        return HttpResponseRedirect(reverse_lazy('owner:shift_select'))