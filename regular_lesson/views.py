from datetime import timedelta, datetime, date
import json

from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import ListView, DeleteView, View, TemplateView
from django.views.generic.edit import CreateView
from django.db.models import Q
from django.utils.decorators import method_decorator
from collections import defaultdict
from django.contrib import messages

from accounts.decorators import user_type_required
from .models import RegularLessonAdmin, Lesson
from students.models import Student
from shift.models import ShiftTemplateLessonRelation
from .forms import RegularLessonAdminCreateForm
from utils.choices import TIME_CHOICES, SUBJECT_CHOICES, DAY_CHOICES, GRADE_CHOICES
from utils.mixins import FiscalYearMixin
from utils.helpers import generate_regular_lessons, get_fiscal_year_boundaries, get_today

@method_decorator(user_type_required(), name='dispatch')
class RegularLessonCreateView(CreateView):
    form_class = RegularLessonAdminCreateForm
    template_name = 'owner/regular_create.html'
    
    def get_initial(self):
        initial = super().get_initial()
        # 今日の日付をstart_dateの初期値として設定
        initial['start_date'] = get_today()
        # 年度末の日付をend_dateの初期値として設定
        _, end_date = get_fiscal_year_boundaries(initial['start_date'])
        initial['end_date'] = end_date
        return initial

    def get_success_url(self):
        return reverse_lazy('owner:regular_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grade_choices'] = GRADE_CHOICES
        context['subject_choices_json'] = json.dumps(SUBJECT_CHOICES)
        context['time_choices_json'] = json.dumps(TIME_CHOICES)
        context['day_choices_json'] = json.dumps(DAY_CHOICES)      
        context['grade_choices_json'] = json.dumps(GRADE_CHOICES)
        return context

    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        pk = json_data['student']
        student = Student.objects.get(pk=pk)
        grade = student.grade
        subject = json_data['subject']
        start_date = datetime.strptime(json_data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(json_data['end_date'], '%Y-%m-%d').date()
        selected_timetable = json_data['selected_timetable']

        _, fiscal_end_date = get_fiscal_year_boundaries(start_date)

        if start_date > end_date:
            return JsonResponse({'error': '開始日は終了日より前にしてください。'})           

        # end_dateを変えれないようにするので不要?
        if end_date > fiscal_end_date:
            return JsonResponse({'error': '終了日は年度末より前にしてください。'})
        
        # 取得コマ数の制限(5コマ以上の場合にエラー)
        if len(RegularLessonAdmin.objects.filter(student=student, end_date=end_date)) + len(selected_timetable) > 5:
           return JsonResponse({'error': '取得授業数が不正です。'})

        # チェックを全て行うため2回書く必要あり
        for timetable in selected_timetable:
            day = int(timetable['day'])
            time = int(timetable['time'])

            if RegularLessonAdmin.objects.filter(student=student, day=day, time=time, end_date=end_date).exists():
                get_day_display = DAY_CHOICES[day-1][1]
                get_time_display = TIME_CHOICES[time-1][1]
                return JsonResponse({'error': f'{get_day_display} {get_time_display}にはすでに授業が入っています。'})

        for timetable in selected_timetable:
            day = int(timetable['day'])
            time = int(timetable['time'])
            regular_lesson_admin = RegularLessonAdmin.objects.create(
                student_id=pk,
                grade=grade,
                subject=subject,
                day=day,
                time=time,
                start_date=start_date,
                end_date=end_date
            )        

            generate_regular_lessons(regular_lesson_admin, day, time, start_date, end_date)

        messages.success(request, "登録できました")
        
        return JsonResponse({'success':True,'redirect_url': self.get_success_url()})

@method_decorator(user_type_required(), name='dispatch')   
class RegularLessonListView(FiscalYearMixin, ListView):
    template_name = 'owner/regular_list.html'
    context_object_name = 'regular_lessons'

    def get_queryset(self):
        today = get_today()
        _, end_date = self.get_fiscal_year_boundaries(today)
        queryset = RegularLessonAdmin.objects.filter(end_date=end_date).order_by('student__grade', 'student', 'day', 'time')
        student_id = self.request.GET.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subject_choices_json'] = json.dumps(SUBJECT_CHOICES)
        context['time_choices_json'] = json.dumps(TIME_CHOICES)
        context['day_choices_json'] = json.dumps(DAY_CHOICES)
        context['students'] = Student.objects.all()      
        context['selected_student_id'] = int(self.request.GET.get('student_id')) if self.request.GET.get('student_id') else None
        return context
    
@method_decorator(user_type_required(), name='dispatch')
class RegularLessonUpdateView(FiscalYearMixin, View):
    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        id = json_data['data_id']
        student_id = json_data['student_id']
        student = Student.objects.get(pk=student_id)
        subject = int(json_data['subject'])
        day = int(json_data['day'])
        time = int(json_data['time'])
        _, end_date = get_fiscal_year_boundaries(get_today())

        # 授業が変更されていない場合の処理
        obj = RegularLessonAdmin.objects.get(id=id)
        if obj.day == day and obj.time == time and obj.subject == subject:
            messages.error(request, '科目、曜日、時間のいずれかを変更してください')
            return JsonResponse({'error': True}, status=405)
  
        # 授業の変更先が存在する場合(科目が同じ場合は無視する)
        if RegularLessonAdmin.objects.filter(student=student, day=day, time=time, end_date=end_date).exclude(id=id).exists():
            get_day_display = DAY_CHOICES[day-1][1]
            get_time_display = TIME_CHOICES[time-1][1]
            messages.error(request, f'{get_day_display} {get_time_display}のコマにはすでに授業が入っています。')
            return JsonResponse({'error': True}, status=405)    

        today = get_today()
        end_date = obj.end_date

        # end_dateを変更したときに即座に変更することで対応
        obj.save()

        # 今日以降のLessonを削除
        Lesson.objects.filter(date__gte=today, date__lte=end_date, regular=obj).delete()

        # シフトテンプレートを削除
        shift_lesson_relation = ShiftTemplateLessonRelation.objects.get(
            Q(template_lesson1=obj) | Q(template_lesson2=obj) |
            Q(template_lesson3=obj) | Q(template_lesson4=obj)
        )

        if shift_lesson_relation.template_lesson1 == obj:
            shift_lesson_relation.template_lesson1 = None
        if shift_lesson_relation.template_lesson2 == obj:
            shift_lesson_relation.template_lesson2 = None
        if shift_lesson_relation.template_lesson3 == obj:
            shift_lesson_relation.template_lesson3 = None
        if shift_lesson_relation.template_lesson4 == obj:
            shift_lesson_relation.template_lesson4 = None

        shift_lesson_relation.save()

        # RegularLessonAdminを前日で終了
        obj.end_date = today
        obj.save()

        # 今日から年度末までの新しいRegularLessonAdminを作成
        _, end_date = self.get_fiscal_year_boundaries(today)
        new_obj = RegularLessonAdmin.objects.create(
            student=student,
            grade=student.grade,
            subject=subject,
            day=day,
            time=time,
            start_date=today,
            end_date= end_date
        )

        generate_regular_lessons(new_obj, day, time, today, end_date)

        messages.success(request, '更新しました。')

        return JsonResponse({'redirect_url': reverse_lazy('owner:regular_list')})

@method_decorator(user_type_required(), name='dispatch')
class RegularLessonCancelView(View):
    def post(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        obj = RegularLessonAdmin.objects.get(pk=pk)

        # 今日以降のLessonを削除
        today = get_today()
        _, end_date = get_fiscal_year_boundaries(today)
        Lesson.objects.filter(date__gte=today, date__lte=end_date, regular=obj).delete()

        # シフトテンプレートを削除
        shift_lesson_relation = ShiftTemplateLessonRelation.objects.get(
            Q(template_lesson1=obj) | Q(template_lesson2=obj) |
            Q(template_lesson3=obj) | Q(template_lesson4=obj)
        )

        if shift_lesson_relation.template_lesson1 == obj:
            shift_lesson_relation.template_lesson1 = None
        if shift_lesson_relation.template_lesson2 == obj:
            shift_lesson_relation.template_lesson2 = None
        if shift_lesson_relation.template_lesson3 == obj:
            shift_lesson_relation.template_lesson3 = None
        if shift_lesson_relation.template_lesson4 == obj:
            shift_lesson_relation.template_lesson4 = None

        shift_lesson_relation.save()

        # RegularLessonAdminを前日で終了
        obj.end_date = today
        obj.save()

        messages.success(request, '中止できました')

        return HttpResponseRedirect(reverse_lazy('owner:regular_list'))

@method_decorator(user_type_required(), name='dispatch')
class RegularLessonDeleteView(DeleteView):
    model = RegularLessonAdmin
    success_url = reverse_lazy('owner:regular_list')
    template_name = 'owner/regular_admin_confirm_delete.html'

@method_decorator(user_type_required(), name='dispatch')
class ParentLessonListView(TemplateView):
    model = Lesson
    template_name = 'parent/schedule_detail.html'
    context_object_name = 'lessons'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_id = self.kwargs['pk']
        
        current_year = get_today().year
        current_month = get_today().month

        start_date = date(current_year, current_month, 1)
        end_date = start_date + timedelta(days=60)

        lessons = Lesson.objects.filter(
            student_id=student_id,
            date__gte=start_date,
            date__lt=end_date
        )

        unique_dates = defaultdict(list)
        for lesson in lessons:
            unique_dates[lesson.date].append(lesson)

        unique_dates_list = [(date, lessons) for date, lessons in unique_dates.items()]

        context['lessons'] = lessons
        context['student_id'] = student_id
        context['current_year'] = current_year
        context['current_month'] = current_month
        context['next_month_year'] = end_date.year
        context['next_month_month'] = end_date.month
        context['unique_dates_list'] = unique_dates_list 

        return context
