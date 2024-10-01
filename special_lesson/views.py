import json
from datetime import timedelta, datetime

from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, TemplateView, CreateView, DeleteView, View
from django.shortcuts import render
from django.contrib import messages

from accounts.decorators import user_type_required
from .models import SpecialLesson, SpecialLessonStudentRequest, SpecialLessonAdmin, SpecialLessonTeacherRequest
from .forms import SpecialLessonAdminCreateForm
from shift.models import Shift
from year_schedule.models import Event
from regular_lesson.models import Lesson
from students.models import Student
from utils.choices import TIME_CHOICES, SPECIAL_TIME_CHOICES, SUBJECT_CHOICES
from utils.helpers import generate_shifts, get_special_ordering

@method_decorator(user_type_required(), name='dispatch')
class SpecialLessonListView(ListView):
    model = SpecialLesson
    context_object_name = 'special_lessons'

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/special_list.html']
    
    def get_queryset(self):
        return SpecialLesson.objects.all()

@method_decorator(user_type_required(), name='dispatch')
class SpecialLessonDetailView(ListView):
    model = SpecialLessonAdmin
    template_name = 'owner/special_detail.html'
    context_object_name = 'special_lesson_admins'

    def get_queryset(self):
        queryset = super().get_queryset()
        pk = self.kwargs['pk']
        queryset = queryset.filter(special_lesson_id=pk)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pk'] = self.kwargs['pk']
        context['subject_choices_json'] = json.dumps(SUBJECT_CHOICES)
        return context
    

@method_decorator(user_type_required(), name='dispatch')
class SpecialLessonCreateView(TemplateView):
    template_name = 'owner/special_create.html'
    success_url = reverse_lazy('owner:special_list')

    def generate_date_list(self, start_date_str, end_date_str):
        # 開始日と終了日の文字列をdatetimeオブジェクトに変換
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # 日付を1日ずつ増やしながらリストに格納
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            # 土曜日か日曜日でなければ日付をリストに追加
            if current_date.weekday() < 5:
                date_list.append(current_date.strftime('%Y-%m-%d'))
            # 日付を1日進める
            current_date += timedelta(days=1)

        return date_list

    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        name = json_data['name']
        start_date = json_data['start_date']
        end_date = json_data['end_date']
        is_extend = json_data['is_extend']
        date_list = self.generate_date_list(start_date, end_date)

        if start_date > end_date:
            return JsonResponse({'message': '開始日は終了日より遅い日付を選択してください。'}, status=400)

        if SpecialLesson.objects.filter(start_date__lte=end_date, end_date__gte=start_date).exists():
            return JsonResponse({'message': '期間が重複しています'}, status=400)

        # 特別講習を作成
        SpecialLesson.objects.create(name=name, start_date=start_date, end_date=end_date, is_extend=is_extend)

        clousure_dates = [obj.date.strftime('%Y-%m-%d') for obj in Event.objects.filter(date__gte=start_date, date__lte=end_date, is_closure=True)]
        for date in date_list:
            if not date in clousure_dates:
                Event.objects.create(title=name, date=date, is_fixed=True)

                date = datetime.strptime(date, '%Y-%m-%d').date()
                generate_shifts(date)
    
        messages.success(self.request, "登録できました")
        return JsonResponse({'message': 'success'})
    
@method_decorator(user_type_required(), name='dispatch') 
class SpecialLessonDeleteView(DeleteView):
    model = SpecialLesson
    success_url = reverse_lazy('owner:special_list')
    template_name = 'owner/special_confirm_delete.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        name = self.object.name
        start_date = self.object.start_date
        end_date = self.object.end_date
        is_extend = self.object.is_extend

        # カレンダーを削除
        Event.objects.filter(title=name, date__gte=start_date, date__lte=end_date, is_fixed=True).delete()

        # Shiftが拡張されている場合に対応するシフトを削除
        if is_extend:
            current_date = start_date
            while current_date <= end_date:

                # 拡張されたシフトのみ削除
                Shift.objects.filter(date=current_date, time__in=[time[0] for time in SPECIAL_TIME_CHOICES]).delete()
                current_date += timedelta(days=1)

        return super().post(request, *args, **kwargs)

@method_decorator(user_type_required(), name='dispatch')
class SpecialLessonAdminCreateView(CreateView):
    model = SpecialLessonAdmin
    form_class = SpecialLessonAdminCreateForm
    template_name = 'owner/special_admin_create.html'

    def generate_date_list(self, start_date, end_date):
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            # 土曜日か日曜日でなければ日付をリストに追加
            if current_date.weekday() < 5:
                date_list.append(current_date.strftime('%Y-%m-%d'))
            # 日付を1日進める
            current_date += timedelta(days=1)

        return date_list
    
    def form_valid(self, form):
        special_lesson_admin = form.save(commit=False)
        special_lesson = SpecialLesson.objects.get(pk=self.kwargs['pk'])
        student = special_lesson_admin.student
        special_lesson_admin.special_lesson = special_lesson
        special_lesson_admin.grade = student.grade
        special_lesson_admin.save()

        if not SpecialLessonStudentRequest.objects.filter(student=student, special_lesson=special_lesson).exists():
            if special_lesson.is_extend:
                time_choices = [time[0] for time in SPECIAL_TIME_CHOICES] + [time[0] for time in TIME_CHOICES]
            else:
                time_choices = [time[0] for time in TIME_CHOICES]
            start_date = special_lesson.start_date
            end_date = special_lesson.end_date
            date_list = self.generate_date_list(start_date, end_date)
            clousure_dates = [obj.date.strftime('%Y-%m-%d') for obj in Event.objects.filter(date__gte=start_date, date__lte=end_date, is_closure=True)]
            for date in date_list:
                if not date in clousure_dates:
                    for time in time_choices:
                        SpecialLessonStudentRequest.objects.create(
                            student=student,
                            special_lesson=special_lesson,
                            date=date,
                            time=time,
                        )

        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pk'] = self.kwargs['pk']
        return context

    def get_success_url(self):
        return reverse_lazy('owner:special_detail', kwargs={'pk': self.kwargs.get('pk')})
  
@method_decorator(user_type_required(), name='dispatch')  
class SpecialLessonAdminUpdateView(View):
    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.POST.get('json_data'))
        id = json_data['id']
        subject = json_data['subject']
        periods = json_data['periods']
        obj = SpecialLessonAdmin.objects.get(id=id)
        obj.subject = subject
        obj.periods = periods
        obj.save()
        pk = self.kwargs['pk']
        return JsonResponse({'redirect_url': reverse_lazy('owner:special_detail', kwargs={'pk': pk})})

@method_decorator(user_type_required(), name='dispatch')
class SpecialLessonAdminDeleteView(DeleteView):
    template_name = 'owner/special_admin_confirm_delete.html'
    model = SpecialLessonAdmin
    
    def get_success_url(self):
        obj = self.get_object()
        pk = obj.special_lesson.pk
        return reverse_lazy('owner:special_detail', kwargs={'pk': pk})

@method_decorator(user_type_required(), name='dispatch')
class SpecialLessonTeacherRequestFormView(TemplateView):

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/special_request_form.html']
     
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        context['pk'] = pk
        special_lesson = SpecialLesson.objects.get(pk=pk)
        requests = SpecialLessonTeacherRequest.objects.filter(teacher=self.request.user, special_lesson=special_lesson).order_by('date', get_special_ordering())
        context['requests'] = requests

        is_extend = special_lesson.is_extend
        if is_extend:
            times = SPECIAL_TIME_CHOICES + TIME_CHOICES
        else:
            times = TIME_CHOICES
        context['times'] = times

        return context
    
    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        pk = self.kwargs['pk']
        special_lesson = SpecialLesson.objects.get(pk=pk)

        for date, times in json_data.items():
            for time, value in times.items():
                time = int(time)
                special =  SpecialLessonTeacherRequest.objects.get(teacher=self.request.user, special_lesson=special_lesson, date=date, time=time)
                special.is_available = value
                special.save()
        
        messages.success(request, "保存しました")
                
        return JsonResponse({'redirect_url': reverse_lazy('teacher:special_lesson_request', kwargs={'pk': pk})})

@method_decorator(user_type_required(), name='dispatch')
class SpecialLessonStudentRequestFormView(TemplateView):

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/special_request_form.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        special_lesson_pk = self.kwargs['special_lesson_pk']
        context['special_lesson_pk'] = special_lesson_pk
        pk = self.kwargs['pk']
        context['pk'] = pk
        special_lesson = SpecialLesson.objects.get(pk=special_lesson_pk)
        requests = SpecialLessonStudentRequest.objects.filter(student=self.request.user.parent_profile.current_student, special_lesson=special_lesson).order_by('date', get_special_ordering())
        context['requests'] = requests

        is_extend = special_lesson.is_extend
        if is_extend:
            times = SPECIAL_TIME_CHOICES + TIME_CHOICES
        else:
            times = TIME_CHOICES
        context['times'] = times

        return context
    
    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        special_lesson_pk = self.kwargs['special_lesson_pk']
        pk = self.kwargs['pk']
        special_lesson = SpecialLesson.objects.get(pk=special_lesson_pk)

        for date, times in json_data.items():
            for time, value in times.items():
                time = int(time)
                special =  SpecialLessonStudentRequest.objects.get(student=self.request.user.parent_profile.current_student, special_lesson=special_lesson, date=date, time=time)
                special.is_available = value
                special.save()
        
        messages.success(request, "保存しました")

        return JsonResponse({'redirect_url': reverse_lazy('parent:special_lesson_request', kwargs={'pk': pk, 'special_lesson_pk': special_lesson_pk})})
    
@method_decorator(user_type_required(), name='dispatch')
class SpecialLessonPrintView(TemplateView):
    template_name = 'owner/special_print.html'

    def generate_date_list(self, start_date, end_date):
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            # 土曜日か日曜日でなければ日付をリストに追加
            if current_date.weekday() < 5:
                date_list.append(current_date)
            # 日付を1日進める
            current_date += timedelta(days=1)

        return date_list

    def get_queryset(self):
        special_lesson_admins = SpecialLessonAdmin.objects.filter(special_lesson_id=self.kwargs['pk'])
        queryset = Lesson.objects.filter(special__in=special_lesson_admins).order_by('student__grade', 'student', 'date', get_special_ordering())
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        special_lesson = SpecialLesson.objects.get(pk=pk)
        special_lesson_admins = SpecialLessonAdmin.objects.filter(special_lesson=special_lesson)
        context['studnets'] = Student.objects.filter(id__in=SpecialLessonAdmin.objects.filter(special_lesson=special_lesson).values('student')).distinct()
        lessons = Lesson.objects.filter(special__in=special_lesson_admins)
        json_data = []
        for lesson in lessons:
            json_data.append({
                'student_id': lesson.student.id,
                'date': f'{lesson.date}',
                'time': lesson.time,
                'subject': lesson.get_subject_display(),
            })
        context['json_data'] = json.dumps(json_data)

        context['pk'] = pk
        context['special_lesson'] = special_lesson
        context['time_choices'] = SPECIAL_TIME_CHOICES + TIME_CHOICES if special_lesson.is_extend else TIME_CHOICES
        start_date = special_lesson.start_date
        end_date = special_lesson.end_date
        events = Event.objects.filter(date__gte=start_date, date__lte=end_date, is_fixed=False)
        json_event = []
        for event in events:
            json_event.append({
                'date': f'{event.date}',
                'title': event.title,
                'is_closure': event.is_closure,
            })
        context['events'] = json.dumps(json_event)
        context['date_list'] = self.generate_date_list(start_date, end_date)
        return context