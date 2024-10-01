import json

from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView
from django.forms import formset_factory
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.contrib import messages

from accounts.decorators import user_type_required
from .models import TestResult, CATEGORY_CHOICES, PROGRAM_CHOICES, COUNT_CHOICES
from students.models import Student

@method_decorator(user_type_required(), name='dispatch')
class VocabularyTestDetailView(ListView):
    model = TestResult
    context_object_name = 'test_results'

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/vocabulary_test_detail.html']

    def get_queryset(self):
        student_id = self.kwargs['pk']
        category_choices = [category[0] for category in CATEGORY_CHOICES]
        program_choices = [program[0] for program in PROGRAM_CHOICES]
        count_choices = [count[0] for count in COUNT_CHOICES]
        
        queryset = []
    
        for category in category_choices:
            for program in program_choices:
                for count in count_choices:
                    obj = TestResult.objects.get(
                        student_id=student_id,
                        category=category,
                        program=program,
                        count=count,
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
class VocabularyTestUpdateView(TemplateView):

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/vocabulary_test_update.html']

    def get_success_url(self):
        pk = self.kwargs['pk']
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        success_url = reverse_lazy(f'{user_type}:vocabulary_test_detail', kwargs={'pk': pk})
        return success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        context['pk'] = pk
        context['student'] = Student.objects.get(pk=pk)
        category_choices = [category[0] for category in CATEGORY_CHOICES]
        program_choices = [program[0] for program in PROGRAM_CHOICES]
        count_choices = [count[0] for count in COUNT_CHOICES]

        # 空のJSONオブジェクトを作成
        json_data = {}
    
        # category_choices、program_choices、count_choices をループで走査
        for category in category_choices:
            # カテゴリーごとにオブジェクトを初期化
            json_data[category] = {}
            for program in program_choices:
                # プログラムごとにオブジェクトを初期化
                json_data[category][program] = {}
                for count in count_choices:
                    # カウントごとにオブジェクトを初期化
                    # ここで TestResult オブジェクトから日付を取得し、JSONに追加する
                    obj = TestResult.objects.get(
                        student_id=pk,
                        category=category,
                        program=program,
                        count=count,
                    )
                    date = obj.date
                    parsed_date = date.strftime('%Y-%m-%d') if date else None

                    score = obj.score
                    fullscore = obj.fullscore

                    # プログラムとカウントに対応するデータを JSON に追加
                    json_data[category][program][count] = {
                        'date': parsed_date,
                        'score': score,
                        'fullscore': fullscore
                    }

        # JSONを文字列に変換
        json_str = json.dumps(json_data)
        
        CATEGORY_CHOICES_list = [[item[0], item[1]] for item in CATEGORY_CHOICES]
        PROGRAM_CHOICES_list = [[item[0], item[1]] for item in PROGRAM_CHOICES]
        COUNT_CHOICES_list = [[item[0], item[1]] for item in COUNT_CHOICES]

        context['json_str'] = json_str
        context['category_choices'] = CATEGORY_CHOICES_list
        context['program_choices'] = PROGRAM_CHOICES_list
        context['count_choices'] = COUNT_CHOICES_list
        return context
    
    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)

        pk = self.kwargs['pk']
    
        category_choices = [category[0] for category in CATEGORY_CHOICES]
        program_choices = [program[0] for program in PROGRAM_CHOICES]
        count_choices = [count[0] for count in COUNT_CHOICES]
        
        for category in category_choices:
            for program in program_choices:
                for count in count_choices:
                    # 各組み合わせに対して処理を行う
                    date = json_data.get(str(category), {}).get(str(program), {}).get(str(count), {}).get("date")
                    score = json_data.get(str(category), {}).get(str(program), {}).get(str(count), {}).get("score")
                    fullscore = json_data.get(str(category), {}).get(str(program), {}).get(str(count), {}).get("fullscore")

                    new_date = date if date else None
                    new_score = score if score else None
                    new_fullscore = fullscore if fullscore else None

                    obj = TestResult.objects.get(
                        student_id=pk,
                        category=category,
                        program=program,
                        count=count,
                    )
    
                    obj.date = new_date
                    obj.score = new_score
                    obj.fullscore = new_fullscore
                    obj.save()

        messages.success(request, "英単語テストの結果を更新しました。")

        return JsonResponse({'redirect_url': reverse_lazy('owner:vocabulary_test_detail', kwargs={'pk': pk})})