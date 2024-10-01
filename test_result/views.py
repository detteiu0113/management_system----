from datetime import date
import json

from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, FormView, TemplateView, UpdateView
from accounts.decorators import user_type_required
from django.http import JsonResponse
from django.contrib import messages

from students.models import Student
from .models import AverageScore, TestResult
from .forms import AverageScoreForm, AverageScoreUpdateForm
from utils.choices import GRADE_CHOICES, SCHOOL_CHOICES
from utils.mixins import FiscalYearMixin
from utils.helpers import get_today, get_fiscal_year_boundaries_april

@method_decorator(user_type_required(), name='dispatch')
class AverageScoreListView(FiscalYearMixin, ListView):
    model = AverageScore
    template_name = 'owner/average_score_list.html'
    context_object_name = 'average_scores'

    def get_queryset(self):
        selected_year = self.request.GET.get('year')
        if selected_year:
            selected_date = date(int(selected_year), 4, 1)
            start_date, end_date = get_fiscal_year_boundaries_april(selected_date)
            queryset = AverageScore.objects.filter(date__gte=start_date, date__lte=end_date)       
        else:
            queryset = AverageScore.objects.all()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if AverageScore.objects.exists():

            # 最も古い年度と最新の年度を取得
            oldest_year = AverageScore.objects.earliest('date').date.year
            latest_year = AverageScore.objects.latest('date').date.year

            # 年度の範囲を作成
            available_years = range(oldest_year-1, latest_year+1)

            # 選択された年度（初期値として最新の年度を選択）
            selected_year = int(self.request.GET.get('year')) if self.request.GET.get('year') else None

            context['available_years'] = available_years
            context['selected_year'] = selected_year

        context['grades'] =  GRADE_CHOICES
        context['schools'] = SCHOOL_CHOICES

        return context
    
@method_decorator(user_type_required(), name='dispatch')
class AverageScoreCreateView(FormView):
    form_class = AverageScoreForm
    template_name = 'owner/average_score_form.html'
    success_url = reverse_lazy('owner:average_score_list')

    def form_valid(self, form):
        school = form.cleaned_data['school']
        grade = form.cleaned_data['grade']
        date = form.cleaned_data['date']
        jap = form.cleaned_data['jap']
        mat = form.cleaned_data['mat']
        soc = form.cleaned_data['soc']
        sci = form.cleaned_data['sci']
        eng = form.cleaned_data['eng']
        five_total = form.cleaned_data['five_total']
        mus = form.cleaned_data['mus']
        art = form.cleaned_data['art']
        phy = form.cleaned_data['phy']
        tec = form.cleaned_data['tec']
        nine_total = form.cleaned_data['nine_total']
        test_name = form.cleaned_data['test_name']
        custom_test_name = form.cleaned_data['custom_test_name']

        if test_name == 'テスト名を入力':
            test_name = custom_test_name
        
        # AverageScoreモデルのインスタンスを作成して保存します
        AverageScore.objects.create(
            school=school,
            grade=grade,
            date=date,
            jap=jap,
            mat=mat,
            soc=soc,
            sci=sci,
            eng=eng,
            five_total=five_total,
            mus=mus,
            art=art,
            phy=phy,
            tec=tec,
            nine_total=nine_total,
            test_name=test_name,
        )
        
         # フラッシュメッセージを追加
        messages.add_message(self.request, messages.SUCCESS, "平均点の登録が完了しました。")
        
        return super().form_valid(form)

@method_decorator(user_type_required(), name='dispatch') 
class AverageScoreUpdateView(UpdateView):
    model = AverageScore
    form_class = AverageScoreUpdateForm
    template_name = 'owner/average_score_update_form.html'
    success_url = reverse_lazy('owner:average_score_list')
    
@method_decorator(user_type_required(), name='dispatch')
class TestResultDetailView(FiscalYearMixin, ListView):
    model = TestResult
    context_object_name = 'test_results'

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/test_result_detail.html']
    
    def get_queryset(self):
        student_id = self.kwargs['pk']
        student = Student.objects.get(id=student_id)
        grade = student.grade
        school = student.school

        today = get_today()
        start_date, end_date = get_fiscal_year_boundaries_april(today)
        
        average_score_choices = AverageScore.objects.filter(grade=grade, school=school, date__gte=start_date, date__lte=end_date).order_by('date')

        queryset = []

        for average_score in average_score_choices:
            obj, created = TestResult.objects.get_or_create(
                student_id=student_id,
                average_score=average_score,
            )
            queryset.append(obj)

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        context['pk'] = pk
        context['student'] = Student.objects.get(pk=pk)
        return context

@method_decorator(user_type_required(), name='dispatch')
class TestResultUpdateView(FiscalYearMixin, TemplateView):
    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/test_result_edit.html']
    
    def get_success_url(self):
        pk = self.kwargs['pk']
        success_url = reverse_lazy('owner:test_result_detail', kwargs={'pk': pk})
        return success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        context['pk'] = pk
        student = Student.objects.get(pk=pk)

        # JSONデータの作成
        json_data = {
            'test_results': []
        }

        # テスト結果のみ4月で年度切り替え
        today = get_today()
        start_date, end_date = get_fiscal_year_boundaries_april(today)

        objs = TestResult.objects.filter(student=student, average_score__date__gte=start_date, average_score__date__lte=end_date).order_by('average_score__date')
        if objs.exists():
            for obj in objs:
                test_name = obj.average_score.test_name
                json_data['test_results'].append({
                    'test_name': test_name,
                    'jap': obj.jap,
                    'mat': obj.mat,
                    'soc': obj.soc,
                    'sci': obj.sci,
                    'eng': obj.eng,
                    'mus': obj.mus,
                    'art': obj.art,
                    'phy': obj.phy,
                    'tec': obj.tec,
                    'jap_rank': obj.jap_rank,
                    'mat_rank': obj.mat_rank,
                    'soc_rank': obj.soc_rank,
                    'sci_rank': obj.sci_rank,
                    'eng_rank': obj.eng_rank,
                    'five_total_rank': obj.five_total_rank,
                    'mus_rank': obj.mus_rank,
                    'art_rank': obj.art_rank,
                    'phy_rank': obj.phy_rank,
                    'tec_rank': obj.tec_rank,
                    'nine_total_rank':obj.nine_total_rank,
                })

        context['json_data'] = json.dumps(json_data)
        return context
    
    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        pk = self.kwargs['pk']
        student = Student.objects.get(pk=pk)

        for test in json_data:
            test_name = test['test_name']
            test_result = test['test_result']
            obj = TestResult.objects.get(student=student, average_score__test_name=test_name)
            obj.jap = test_result['jap']
            obj.mat = test_result['mat']
            obj.soc = test_result['soc']
            obj.sci = test_result['sci']
            obj.eng = test_result['eng']
            obj.mus = test_result['mus']
            obj.art = test_result['art']
            obj.phy = test_result['phy']
            obj.tec = test_result['tec']
            obj.jap_rank = test_result['jap_rank']
            obj.mat_rank = test_result['mat_rank']
            obj.soc_rank = test_result['soc_rank']
            obj.sci_rank = test_result['sci_rank']
            obj.eng_rank = test_result['eng_rank']
            obj.five_total_rank = test_result['five_total_rank']
            obj.mus_rank = test_result['mus_rank']
            obj.art_rank = test_result['art_rank']
            obj.phy_rank = test_result['phy_rank']
            obj.tec_rank = test_result['tec_rank']
            obj.nine_total_rank = test_result['nine_total_rank']
            obj.save()
        
        messages.success(request, "編集完了できました")

        return JsonResponse({'redirect_url': reverse_lazy('owner:test_result_detail', kwargs={'pk': pk})})
        
@method_decorator(user_type_required(), name='dispatch')
class BatchTestResultUpdateView(TemplateView):
    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/test_result_form.html']
    
    def get_success_url(self):
        average_score_pk = self.kwargs['average_score_pk']
        success_url = reverse_lazy('owner:test_result_form', kwargs={'average_score_pk': average_score_pk})
        return success_url
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        context['pk'] = pk
        average_score = AverageScore.objects.get(pk=pk)
        school = average_score.school
        grade = average_score.grade
        students = Student.objects.filter(school=school, grade=grade)

        # 空のJSONオブジェクトを作成
        json_data = {
            'test_results': []
        }

        for student in students:
            obj, created = TestResult.objects.get_or_create(student=student, average_score=average_score)
            json_data['test_results'].append({
                    'student_name': f'{student.last_name} {student.first_name}',
                    'jap': obj.jap,
                    'mat': obj.mat,
                    'soc': obj.soc,
                    'sci': obj.sci,
                    'eng': obj.eng,
                    'mus': obj.mus,
                    'art': obj.art,
                    'phy': obj.phy,
                    'tec': obj.tec,
                    'jap_rank': obj.jap_rank,
                    'mat_rank': obj.mat_rank,
                    'soc_rank': obj.soc_rank,
                    'sci_rank': obj.sci_rank,
                    'eng_rank': obj.eng_rank,
                    'five_total_rank': obj.five_total_rank,
                    'mus_rank': obj.mus_rank,
                    'art_rank': obj.art_rank,
                    'phy_rank': obj.phy_rank,
                    'tec_rank': obj.tec_rank,
                    'nine_total_rank': obj.nine_total_rank,
                    'student_id': student.id,
            })

        # JSONを文字列に変換
        context['json_data'] = json.dumps(json_data)
        context['students'] = students
        return context
    
    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.POST.get('json_data'))
        pk = self.kwargs['pk']
        average_score = AverageScore.objects.get(pk=pk)
        for test in json_data:
            student_id = test['student_id']
            test_result = test['test_result']
            obj = TestResult.objects.get(student_id=student_id, average_score=average_score)
            obj.jap = test_result['jap']
            obj.mat = test_result['mat']
            obj.soc = test_result['soc']
            obj.sci = test_result['sci']
            obj.eng = test_result['eng']
            obj.mus = test_result['mus']
            obj.art = test_result['art']
            obj.phy = test_result['phy']
            obj.tec = test_result['tec']
            obj.jap_rank = test_result['jap_rank']
            obj.mat_rank = test_result['mat_rank']
            obj.soc_rank = test_result['soc_rank']
            obj.sci_rank = test_result['sci_rank']
            obj.eng_rank = test_result['eng_rank']
            obj.five_total_rank = test_result['five_total_rank']
            obj.mus_rank = test_result['mus_rank']
            obj.art_rank = test_result['art_rank']
            obj.phy_rank = test_result['phy_rank']
            obj.tec_rank = test_result['tec_rank']
            obj.nine_total_rank = test_result['nine_total_rank']
            obj.save()

        messages.success(request, "編集完了しました")

        return JsonResponse({'redirect_url': reverse_lazy('owner:test_result_form', kwargs={'pk': pk})})
