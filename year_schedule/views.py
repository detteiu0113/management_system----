from datetime import date, time, timedelta, datetime
import calendar
import json

from django.utils.decorators import method_decorator
from django.views.generic import View, TemplateView
from django.utils.dateparse import parse_datetime
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.contrib import messages

from accounts.decorators import user_type_required
from .models import Event
from .forms import PrintMonthScheduleForm
from students.models import Student
from regular_lesson.models import Lesson, RegularLessonAdmin
from special_lesson.models import SpecialLessonAdmin, SpecialLesson
from teacher_shift.models import TemporalyShift, TeacherShift
from shift.models import Shift
from utils.mixins import FiscalYearMixin
from utils.helpers import get_today, generate_shifts, get_fiscal_year_boundaries

@method_decorator(user_type_required(), name='dispatch')
class OwnerYearScheduleView(TemplateView):
    template_name = 'owner/year_schedule.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        events = []

        today = get_today()
        start_date, end_date = get_fiscal_year_boundaries(today)

        created_events = Event.objects.all()
        
        for event in created_events:
            # 休校を一番上に持ってくる
            start = event.date.isoformat() if not event.is_closure else f'{event.date.isoformat()}T00:00:00'
            end = event.date.isoformat() if not event.is_closure else f'{event.date.isoformat()}T00:00:01'
            is_fixed = 'true' if event.is_fixed else 'false'
            color = 'red' if event.is_closure else 'black'
            events.append({
                'title': event.title,
                'start': start,
                'end': end,
                'allDay': 'false',
                'backgroundColor': 'transparent',
                'borderColor': 'transparent',
                'textColor': color,
                'extendedProps': {
                    'eventId': event.id,
                    'isFixed': is_fixed
                }
            })
        context['events'] = events
        context['year'] = start_date.year
        return context
    
@method_decorator(user_type_required(), name='dispatch')
class TeacherYearScheduleView(TemplateView):
    template_name = 'teacher/shift_calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.request.user

        today = get_today()
        start_date, end_date = get_fiscal_year_boundaries(today)
        teacher_shifts = TeacherShift.objects.filter(date__gte=start_date, date__lte=end_date, teacher=teacher)

        events = []
        for event in Event.objects.filter(date__gte=start_date, date__lte=end_date):
            start = datetime.combine(event.date, time.min).isoformat()
            end = (datetime.combine(event.date, time.min) + timedelta(minutes=1)).isoformat()
            events.append({
                'title': event.title,
                'start': start,
                'end': end,
                'allDay': 'true',
                'color': 'red',
            })
            
        for teacher_shift in teacher_shifts:
            shift_time = teacher_shift.get_time_display()
            start_time, end_time = shift_time.split('-')
            start = f"{teacher_shift.date}T{start_time}:00"
            end = f"{teacher_shift.date}T{end_time}:00"
            title = f'{start_time}-{end_time}'
            events.append({
                'title': title,
                'start': start,
                'end': end,
                'allDay': 'false',
                'backgroundColor': 'transparent',
                'borderColor': 'transparent',
            })

        context['events'] = events
        return context

@method_decorator(user_type_required(), name='dispatch')
class ParentYearScheduleView(FiscalYearMixin, TemplateView):
    template_name = 'parent/schedule_calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        today = get_today()
        start_date, end_date = get_fiscal_year_boundaries(today)
        student = Student.objects.get(pk=self.request.user.parent_profile.current_student.pk)
        lessons = Lesson.objects.filter(date__gte=start_date, date__lte=end_date, student=student)
        
        events = []
        for event in Event.objects.exclude(hidden=student):
            start = datetime.combine(event.date, time.min).isoformat()
            end = (datetime.combine(event.date, time.min) + timedelta(minutes=1)).isoformat()
            events.append({
                'title': event.title,
                'start': start,
                'end': end,
                'allDay': 'true',
                'color': 'red',
            })

        for lesson in lessons:
            start_time, end_time = lesson.get_time_display().split('-')
            start_datetime = f"{lesson.date}T{start_time}"
            end_datetime = f"{lesson.date}T{end_time}"
            events.append({
                'title': f'{start_time}-{end_time} {lesson.get_subject_display()}',
                'start': start_datetime,
                'end': end_datetime,
                'allDay': 'false',
                'backgroundColor': 'transparent',
                'borderColor': 'transparent',
            })

        context['events'] = events
        return context

@method_decorator(user_type_required(), name='dispatch')
class EventCreateView(View):
    def post(self, request, *args, **kwargs):
        # Ajaxリクエストからデータを取得
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        dates = json_data['dates']
        title = json_data['title']
        is_closure = json_data['is_closure']

        for date in dates:
            # 新しいEventオブジェクトを作成
            event = Event.objects.create(title=title, date=date, is_closure=is_closure)

            if is_closure:
                # 該当する日付のlessonを削除
                Lesson.objects.filter(date=date).delete()

                # 該当する日付のTeacher Shift(臨時を含む)を削除
                TemporalyShift.objects.filter(date=date).delete()

                # シフトを削除
                Shift.objects.filter(date=date).delete()

                # 他のイベントを削除(休校自身のインスタンスを残す)
                Event.objects.filter(date=date, is_closure=False).delete()

        messages.success(request, f'新規予定「{title}」を追加しました。')

        # レスポンスを返す
        return JsonResponse({'status': 'success', 'event_id': event.id})
    
@method_decorator(user_type_required(), name='dispatch')
class EventDeleteView(View):
    def post(self, request, *args, **kwargs):
        # Ajaxリクエストからデータを取得
        event_id = request.POST.get('event_id')
        event = Event.objects.get(id=event_id)
        date = event.date

        #　休校の場合は元のシフト(講習授業の拡張を含む)を復元
        if event.is_closure:
            generate_shifts(date)

            # 特別講習期間のイベントを復元
            if SpecialLesson.objects.filter(start_date__lte=date, end_date__gte=date).exists():
                special_lesson = SpecialLesson.objects.get(start_date__lte=date, end_date__gte=date)
                name = special_lesson.name
                Event.objects.create(
                    title=name,
                    date=date,
                    is_fixed=True,
                )

        event.delete()

        messages.success(request, '削除しました')

        return JsonResponse({'status': 'success'})
    
@method_decorator(user_type_required(), name='dispatch')
class PrintSelectView(TemplateView):
    template_name = 'owner/print_select.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PrintMonthScheduleForm
        return context

    def post(self, request, *args, **kwargs):
        year = request.POST.get('year')
        month = request.POST.get('month')
        return HttpResponseRedirect(reverse_lazy('owner:print_month_schedule', kwargs={'year': year, 'month': month}))

@method_decorator(user_type_required(), name='dispatch')
class PrintMonthScheduleView(TemplateView):
    template_name = 'owner/print_month_schedule.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs['year']
        month = self.kwargs['month']
        start_date_of_month = date(year, month, 1)
        end_date_of_month = date(year, month, calendar.monthrange(year, month)[1])
        students = Student.objects.filter(is_on_leave=False, is_withdrawn=False)
        all_events = []
        for student in students:
            lessons = Lesson.objects.filter(date__gte=start_date_of_month, date__lte=end_date_of_month, student=student)
            obj = {}
            events = []

            # 全体イベント
            for event in Event.objects.exclude(hidden=student):
                start = datetime.combine(event.date, time.min).isoformat()
                end = (datetime.combine(event.date, time.min) + timedelta(minutes=1)).isoformat()
                print(start, end)
                events.append({
                    'title': event.title,
                    'start': start,
                    'end': end,
                    'allDay': 'false',
                    'backgroundColor': 'transparent',
                    'borderColor': 'transparent',
                    'textColor': 'red',
                })

            for lesson in lessons:
                start_time, end_time = lesson.get_time_display().split('-')
                start = f"{lesson.date}T{start_time}:00"
                end = f"{lesson.date}T{end_time}:00"
                print(start, end)
                events.append({
                    'title': f'{start_time}-{end_time} {lesson.get_subject_display()}',
                    'start': start,
                    'end': end,
                    'allDay': 'false',
                    'backgroundColor': 'transparent',
                    'borderColor': 'transparent',
                    'textColor': 'black',
                })

            obj['student'] = f'{student.last_name} {student.first_name}'
            obj['events'] = events
            all_events.append(obj)
            
        context['json_str'] = json.dumps(all_events)
        context['year'] = year
        context['month'] = month
        context['start_date'] = start_date_of_month.strftime('%Y-%m-%d')
        context['end_date'] = (end_date_of_month + timedelta(days=1)).strftime('%Y-%m-%d')
        return context