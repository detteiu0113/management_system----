import json

from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.generic import ListView, TemplateView
from django.contrib import messages
from accounts.decorators import user_type_required
from .models import ReportGrade, SEMESTER_CHOICES, SUBJECT_CHOICES
from students.models import Student
from utils.choices import GRADE_CHOICES

@method_decorator(user_type_required('owner', 'teacher', 'parent'), name='dispatch')
class ReportCardDetailView(ListView):
    model = ReportGrade
    context_object_name = 'grades'

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/report_card_detail.html']

    def get_queryset(self):
        student_id = self.kwargs['pk']
        semester_choices = [semester[0] for semester in SEMESTER_CHOICES]
        subject_choices = [subject[0] for subject in SUBJECT_CHOICES]

        queryset = []
    
        for semester in semester_choices:
            for subject in subject_choices:
                obj, _ = ReportGrade.objects.get_or_create(
                    student_id=student_id,
                    semester=semester,
                    subject=subject,
                )
                queryset.append(obj)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        context['pk'] = pk
        context['student'] = Student.objects.get(pk=pk)
        return context
    
@method_decorator(user_type_required('owner', 'teacher', 'parent'), name='dispatch')
class ReportCardUpdateView(TemplateView):

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/report_card_edit.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pk = self.kwargs['pk']
        context['pk'] = pk
        context['student'] = Student.objects.get(pk=pk)

        semester_choices = [semester[0] for semester in SEMESTER_CHOICES]
        subject_choices = [subject[0] for subject in SUBJECT_CHOICES]

        # 空のJSONオブジェクトを作成
        json_data = {}

        # category_choices、program_choices、count_choices をループで走査
        for semester in semester_choices:
            # カテゴリーごとにオブジェクトを初期化
            json_data[semester] = {}
            for subject in subject_choices:
                # プログラムごとにオブジェクトを初期化
                json_data[semester][subject] = {}
                obj = ReportGrade.objects.get(
                    student_id=pk,
                    semester=semester,
                    subject=subject,
                )
                value = obj.value

                # プログラムとカウントに対応するデータを JSON に追加
                json_data[semester][subject]['value'] = value

        # JSONを文字列に変換
        json_str = json.dumps(json_data)
        context['json_str'] = json_str

        semester_choices_list = [[item[0], item[1]] for item in SEMESTER_CHOICES]
        subject_choices_list = [[item[0], item[1]] for item in SUBJECT_CHOICES]
        
        context['semester_choices'] = semester_choices_list
        context['subject_choices'] = subject_choices_list
        return context
    
    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)

        pk = self.kwargs['pk']

        semester_choices = [semester[0] for semester in SEMESTER_CHOICES]
        subject_choices = [subject[0] for subject in SUBJECT_CHOICES]

        for semester in semester_choices:
            for subject in subject_choices:
                value = json_data.get(str(semester), {}).get(str(subject)) or None

                obj = ReportGrade.objects.get(
                    student_id=pk,
                    semester=semester,
                    subject=subject,
                )
                obj.value = value
                obj.save()

        messages.success(request, "編集完了しました")
        
        return JsonResponse({'redirect_url': reverse_lazy('owner:report_card_detail', kwargs={'pk': pk})})
    
@method_decorator(user_type_required(), name='dispatch')
class BatchReportCardSelectView(TemplateView):
    template_name = 'owner/report_card_semester.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['semesters'] = SEMESTER_CHOICES
        return context

@method_decorator(user_type_required(), name='dispatch')
class BatchReportCardUpdateView(TemplateView):

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/report_card_data.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grades'] = [grade[1] for grade in GRADE_CHOICES]
        semester = self.kwargs['semester']
        context['semester'] = semester
        # 中学生をフィルタリング
        if 1 <= int(semester) <= 3:
            grade = 7
        elif 4 <= int(semester) <= 6:
            grade = 8
        else:
            grade = 9
        students = Student.objects.filter(grade=grade)
        student_list = []
        for student in students:
            student_list.append([student.pk, f'{student.last_name} {student.first_name}'])

        subject_choices = [category[0] for category in SUBJECT_CHOICES]

        # 空のJSONオブジェクトを作成
        json_data = {}

        for student in students:
            json_data[student.pk] = {}

            for subject in subject_choices:
                json_data[student.pk][subject] = {}
                obj = ReportGrade.objects.get(
                    student_id=student.pk,
                    subject=subject,
                    semester=semester
                )
                value = obj.value
                # プログラムとカウントに対応するデータを JSON に追加
                json_data[student.pk][subject] = {
                    'value': value
                }

        # JSONを文字列に変換
        json_str = json.dumps(json_data)

        SUBJECT_CHOICES_list = [[item[0], item[1]] for item in SUBJECT_CHOICES]

        context['json_str'] = json_str
        context['students'] = student_list
        context['subject_choices'] = SUBJECT_CHOICES_list

        return context
    
    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        
        semester = self.kwargs['semester']
        subject_choices = [category[0] for category in SUBJECT_CHOICES]

        students = Student.objects.filter(grade__in=[7, 8, 9])
        for student in students:
            for subject in subject_choices:
                value = json_data.get(str(student.pk), {}).get(str(subject)) or None
                obj = ReportGrade.objects.get(
                    student=student,
                    semester=semester,
                    subject=subject,
                )
                obj.value = value
                obj.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            messages.success(request, "編集完了しました")

        return JsonResponse({'redirect_url': reverse_lazy('owner:report_card_form', kwargs={'semester': semester})})
