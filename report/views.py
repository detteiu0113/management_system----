from datetime import date
import calendar
import json

from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView, FormView, TemplateView, View
from django.db.models import Q

from .forms import ReportForm, TestResultForm
from .models import Report
from accounts.decorators import user_type_required
from shift.models import Shift
from students.models import Student
from regular_lesson.models import Lesson
from utils.choices import GRADE_CHOICES
from vocabulary_test.models import TestResult
from utils.helpers import get_today

@method_decorator(user_type_required(), name='dispatch')
class ReportListView(ListView):
    model = Report
    context_object_name = 'reports'

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/report_detail.html']

    def get_queryset(self):
        pk = self.kwargs['pk']
        month = self.request.GET.get('month')
        queryset = super().get_queryset()
        queryset = queryset.filter(student__pk=pk)
        if month:
            today = get_today()
            year = today.year
            month = int(month)
            start_date = date(year, month, 1)
            _, last_day = calendar.monthrange(year, month)
            end_date = date(year, month, last_day)
            queryset = queryset.filter(lesson__date__gte=start_date, lesson__date__lte=end_date)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        context['pk'] = pk
        context['student'] = Student.objects.get(pk=pk)
        return context

@method_decorator(user_type_required(), name='dispatch')
class OwnerSubmitReportListView(ListView):
    model = Report
    template_name = 'owner/report_form_data.html'
    context_object_name = 'reports'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grades'] = GRADE_CHOICES
        context['students'] = Student.objects.all()
        context['today'] = get_today().isoformat()
        return context
    
    def japanese_date(self, value):
        months = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
        return f"{months[value.month - 1]}{value.day}日"
    
@method_decorator(user_type_required(), name='dispatch')
class SubmitReportDeleteView(View):
    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.body)
        for pk in json_data:
            pk = int(pk)
            report = Report.objects.filter(pk=pk)
            lesson = report.lesson

            # 報告済みから削除
            lesson.is_reported = False
            lesson.save()
            report.delete()

        return JsonResponse({'success': True})
    
@method_decorator(user_type_required(), name='dispatch')
class TeacherSubmitReportListView(TemplateView):
    template_name = 'teacher/submit_report_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unreported_lessons = []
        reported_lessons = []
        teacher = self.request.user
        # 一時的に変更
        today = get_today()
        shifts = Shift.objects.filter(teacher_shift__teacher=teacher, date=today) 
        for shift in shifts:
            lessons = shift.lessons
            if lessons:
                if lessons.lesson1:
                    if lessons.lesson1.is_reported:
                        reported_lessons.append(lessons.lesson1)
                    else:
                        unreported_lessons.append(lessons.lesson1)
                if lessons.lesson2:
                    if lessons.lesson2.is_reported:
                        reported_lessons.append(lessons.lesson2)
                    else:
                        unreported_lessons.append(lessons.lesson2)
                if lessons.lesson3:
                    if lessons.lesson3.is_reported:
                        reported_lessons.append(lessons.lesson3)
                    else:
                        unreported_lessons.append(lessons.lesson3)
                if lessons.lesson4:
                    if lessons.lesson4.is_reported:
                        reported_lessons.append(lessons.lesson4)
                    else:
                        unreported_lessons.append(lessons.lesson4)
        context['lessons'] = unreported_lessons
        context['reported_lessons'] = reported_lessons
        return context
        
@method_decorator(user_type_required(), name='dispatch')
class SubmitReportCreateView(FormView):
    template_name = 'teacher/submit_report.html'
    form_class = ReportForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lesson'] = Lesson.objects.get(pk=self.kwargs.get('pk'))
        return context

    def post(self, request, *args, **kwargs):
        report_form = ReportForm(request.POST)
 
        if report_form.is_valid():
            report_instance = report_form.save(commit=False)

            # LessonからStudentオブジェクトを取得する
            lesson = Lesson.objects.get(pk=self.kwargs.get('pk'))
            student_id = lesson.student.id
            student = Student.objects.get(id=student_id)

            # Reportに情報を追加する
            report_instance.lesson = lesson
            report_instance.student = student
            report_instance.teacher = request.user

            # Reportを保存する
            report_instance.save()

            # 授業を報告済みに設定
            lesson.is_reported = True
            lesson.save()

            return HttpResponseRedirect(reverse_lazy('teacher:submit_report_list'))
        
@method_decorator(user_type_required(), name='dispatch')
class SubmitReportUpdateView(UpdateView):
    model = Report
    form_class = ReportForm

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/submit_report.html']
    
    def get_success_url(self):
        if self.request.user.is_owner:
            return reverse_lazy('owner:report_form_data')
        else:
            return reverse_lazy('teacher:submit_report_list')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lesson'] = Report.objects.get(pk=self.kwargs.get('pk')).lesson
        return context

@method_decorator(user_type_required(), name='dispatch')
class SubmitVocabularyTestCreateView(FormView):
    template_name = 'teacher/submit_vocabulary_test.html'
    form_class = TestResultForm

    def post(self, request, *args, **kwargs):
        test_result_form = TestResultForm(request.POST)

        if test_result_form.is_valid():
            test_result_instance_data = test_result_form.cleaned_data
            student = test_result_instance_data.get('student')
            category = test_result_instance_data.get('category')
            program = test_result_instance_data.get('program')
            score = test_result_instance_data.get('score')
            fullscore = test_result_instance_data.get('fullscore')

            # 4回分のテスト結果を取得
            test_results = TestResult.objects.filter(
                student_id=student,
                category=category,
                program=program,
            )

            # 実施日がNoneのテストに登録(4回以上実施の場合は4回目に登録)
            for test_result in test_results:
                if test_result.date == None:
                    test_result_instance = test_result
                    break
            else:
                test_result_instance = test_results[-1]

            test_result_instance.date = get_today()
            test_result_instance.score = score
            test_result_instance.fullscore = fullscore
            test_result_instance.save()

        return HttpResponseRedirect(reverse_lazy('teacher:submit_report_list'))