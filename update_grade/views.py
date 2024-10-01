from datetime import date
from dateutil.relativedelta import relativedelta
import json

from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, View, TemplateView
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.db import IntegrityError

from accounts.decorators import user_type_required
from .forms import StudentUpdateForm
from students.models import Student
from regular_lesson.models import RegularLessonAdmin
from teacher_shift.models import FixedShift
from shift.models import ShiftTemplate
from regular_lesson.models import Lesson
from year_schedule.models import Event
from utils.choices import TIME_CHOICES, SUBJECT_CHOICES, DAY_CHOICES
from utils.helpers import generate_regular_lessons, get_today, generate_teacher_shifts
from utils.mixins import FiscalYearMixin

@method_decorator(user_type_required(), name='dispatch')
class UpdateStudentListView(ListView):
    model = Student
    template_name = 'owner/update_student_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grade_6_students'] = Student.objects.filter(grade=6)
        context['grade_9_students'] = Student.objects.filter(grade=9)
        context['grade_12_students'] = Student.objects.filter(grade=12)
        return context

@method_decorator(user_type_required(), name='dispatch')
class UpdateStudentToMiddleView(UpdateView):
    model = Student
    template_name = 'owner/update_to_middle.html'
    form_class = StudentUpdateForm

    def form_valid(self, form):
        instance = form.instance
        instance.is_upgraded = True
        instance.save()
        messages.success(self.request, '送信完了しました')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('owner:update_student_list')

@method_decorator(user_type_required(), name='dispatch')
class UpdateStudentToHighView(UpdateView):
    model = Student
    template_name = 'owner/update_to_high.html'
    fields = ['high_school']

    def form_valid(self, form):
        instance = form.instance
        instance.is_upgraded = True
        instance.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('owner:update_student_list')
    
@method_decorator(user_type_required(), name='dispatch')
class UpdateStudentToGradView(UpdateView):
    model = Student
    template_name = 'owner/update_to_grad.html'
    fields = ['is_planning_to_withdraw']

    def form_valid(self, form):
        instance = form.instance
        instance.is_upgraded = True
        instance.save()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('owner:update_student_list')
    
@method_decorator(user_type_required(), name='dispatch') 
class UpdateRegularLessonListView(FiscalYearMixin, ListView):
    model = RegularLessonAdmin
    context_object_name = 'regular_lessons'
    template_name = 'owner/update_regular_list.html'

    def get_queryset(self):
        today = get_today()
        _, end_date = self.get_fiscal_year_boundaries(today)
        return RegularLessonAdmin.objects.filter(end_date=end_date, is_upgraded=False).order_by('student__grade', 'student', 'day', 'time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = get_today()
        _, end_date = self.get_fiscal_year_boundaries(today + relativedelta(years=1))

        # 来年度の受講を表示
        context['upgraded_regular_lessons'] = RegularLessonAdmin.objects.filter(end_date=end_date, is_upgraded=False).order_by('student__grade', 'student', 'day', 'time')
        context['subject_choices_json'] = json.dumps(SUBJECT_CHOICES)
        context['time_choices_json'] = json.dumps(TIME_CHOICES)
        context['day_choices_json'] = json.dumps(DAY_CHOICES)      

        return context

@method_decorator(user_type_required(), name='dispatch')
class UpdateRegularLessonContinueView(FiscalYearMixin, View):

    def post(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        obj =  RegularLessonAdmin.objects.get(pk=pk)     
        student = obj.student
        grade = obj.grade
        subject = obj.subject
        day = obj.day
        time = obj.time
        today = get_today()   
        # 来年度の最初と最後の日を取得
        start_date, end_date = self.get_fiscal_year_boundaries(today + relativedelta(years=1))

        if RegularLessonAdmin.objects.filter(student=obj.student, day=obj.day, time=obj.time, end_date=end_date).exclude(pk=pk).exists():
            messages.error(request, 'このコマにはすでに授業が入っています。')
            return HttpResponseRedirect(reverse_lazy('owner:update_regular_list'))

        obj.is_upgraded = True
        obj.save()

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

        generate_regular_lessons(regular_lesson_admin, day, time, start_date, end_date, is_next_year=True)

        messages.success(request, '継続処理が完了しました。')
        return HttpResponseRedirect(reverse_lazy('owner:update_regular_list'))

@method_decorator(user_type_required(), name='dispatch')     
class UpdateRegularLessonUpdateView(FiscalYearMixin, View):
    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        id = json_data['data_id']
        student_id = json_data['student_id']
        student = Student.objects.get(pk=student_id)
        subject = json_data['subject']
        day = json_data['day']
        time = json_data['time']

        today = get_today()
        start_date, end_date = self.get_fiscal_year_boundaries(today + relativedelta(years=1))

        obj = RegularLessonAdmin.objects.get(id=id)
        # 同じ生徒が同じ曜日、時間に変更しようとしているかをチェック
        if RegularLessonAdmin.objects.filter(student=student, day=day, time=time, end_date=end_date).exists():
            return JsonResponse({'message': 'このコマにはすでに授業が入っています。'}, status=400)
        obj.is_upgraded = True
        obj.save()

        grade = student.grade

        if grade == 13:
            new_grade = 13
        else:
            new_grade = grade + 1

        # 来年のRegularLessonAdminを作成
        new_obj = RegularLessonAdmin.objects.create(
            student=student,
            grade=new_grade,
            subject=subject,
            day=day,
            time=time,
            start_date=start_date,
            end_date= end_date
        )

        # is_next_yearで来年度のShiftTemplateに登録
        generate_regular_lessons(new_obj, day, time, start_date, end_date, is_next_year=True)

        messages.success(request, '変更処理が完了しました')

        return JsonResponse({'redirect_url': reverse_lazy('owner:update_regular_list')})

@method_decorator(user_type_required(), name='dispatch')   
class UpdateRegularLessonDeleteView(View):
    def post(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        obj = RegularLessonAdmin.objects.get(pk=pk)
        obj.is_upgraded = True
        obj.save()
        messages.success(request, '終了しました')
        return HttpResponseRedirect(reverse_lazy('owner:update_regular_list'))


@method_decorator(user_type_required(), name='dispatch') 
class UpdateFixedShiftListView(FiscalYearMixin, ListView):
    model = FixedShift
    context_object_name = 'fixed_shifts'
    template_name = 'owner/update_fixed_shift_list.html'

    def get_queryset(self):
        today = get_today()
        _, end_date = self.get_fiscal_year_boundaries(today)
        return FixedShift.objects.filter(end_date=end_date, is_upgraded=False).order_by('teacher', 'day', 'time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = get_today()
        _, end_date = self.get_fiscal_year_boundaries(today + relativedelta(years=1))

        # 来年度のシフトを表示
        context['upgraded_fixed_shifts'] = FixedShift.objects.filter(end_date=end_date, is_upgraded=False).order_by('teacher', 'day', 'time')
        context['subject_choices_json'] = json.dumps(SUBJECT_CHOICES)
        context['time_choices_json'] = json.dumps(TIME_CHOICES)
        context['day_choices_json'] = json.dumps(DAY_CHOICES)

        return context
    
@method_decorator(user_type_required(), name='dispatch') 
class UpdateFixedShiftContinueView( FiscalYearMixin, View):

    def post(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        obj =  FixedShift.objects.get(pk=pk)
        teacher = obj.teacher
        day = obj.day
        time = obj.time
        today = get_today()
        # 来年度の最初と最後の日を取得
        start_date, end_date = self.get_fiscal_year_boundaries(today + relativedelta(years=1))

        if FixedShift.objects.filter(teacher=teacher, day=day, time=time, end_date=end_date).exists():
            messages.error(request, 'このコマにはすでに授業が入っています。')
            return HttpResponseRedirect(reverse_lazy('owner:update_shift_list'))

        obj.is_upgraded = True
        obj.save()

        fixed_shift = FixedShift.objects.create(
            teacher=teacher,
            day=day,
            time=time,
            start_date=start_date,
            end_date=end_date
        )
        generate_teacher_shifts(fixed_shift, day, time, start_date, end_date, is_next_year=True)

        messages.success(request, '継続処理が完了しました')

        return HttpResponseRedirect(reverse_lazy('owner:update_shift_list'))
    
@method_decorator(user_type_required(), name='dispatch')
class UpdateFixedShiftUpdateView(FiscalYearMixin, View):
    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        id = json_data['shift_id']
        day = json_data['day']
        time = json_data['time']

        obj = FixedShift.objects.get(id=id)
        
        teacher = obj.teacher
        today = get_today()

        # 来年のRegularLessonAdminを作成
        start_date, end_date = self.get_fiscal_year_boundaries(today + relativedelta(years=1))

        if FixedShift.objects.filter(teacher=teacher, day=day, time=time, end_date=end_date).exists():
            return JsonResponse({'message': '同じ講師が同じ曜日、時間に変更することはできません。'}, status=400)
        
        obj.is_upgraded = True
        obj.save()

        new_obj = FixedShift.objects.create(
            teacher=teacher,
            day=day,
            time=time,
            start_date=start_date,
            end_date= end_date
        )
        # is_next_yearで来年度のShiftTemplateに登録
        generate_teacher_shifts(new_obj, day, time, start_date, end_date, is_next_year=True)

        messages.add_message(self.request, messages.SUCCESS, "変更処理が完了しました")

        return JsonResponse({'redirect_url': reverse_lazy('owner:update_shift_list')})
    
@method_decorator(user_type_required(), name='dispatch')   
class UpdateFixedShiftDeleteView(View):
    def post(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        obj = FixedShift.objects.get(pk=pk)
        obj.is_upgraded = True
        obj.save()
        messages.success(request, '終了しました')
        return HttpResponseRedirect(reverse_lazy('owner:update_shift_list'))
    
@method_decorator(user_type_required(), name='dispatch') 
class UpdateShiftTemplateView(ListView):
    model = ShiftTemplate
    context_object_name = 'shifts'
    template_name = 'owner/update_shift_template.html'
    paginate_by = 30

    def get_queryset(self):
        return ShiftTemplate.objects.filter(is_next_year=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_choices'] = [time[1] for time in TIME_CHOICES]
        # context['day_choices'] = [day[1] for day in DAY_CHOICES]
        return context
    
@method_decorator(user_type_required(), name='dispatch')
class UpdateYearScheduleView(TemplateView):
    template_name = 'owner/update_year_schedule.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        events = []
        
        for event in Event.objects.all():
            start = event.date.isoformat()
            end = event.date.isoformat()
            events.append({
                'title': event.title,
                'start': start,
                'end': end,
                'allDay': 'false',
                'color': '#E47915',
            })
        context['events'] = events
        return context