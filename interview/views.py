import json

from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.urls import reverse_lazy

from accounts.decorators import user_type_required
from .models import Interview, InterviewRequest, InterviewSchdule, TimeChoice

@method_decorator(user_type_required(), name='dispatch')
class InterviewCreateView(TemplateView):
    template_name = 'owner/interview_create.html'  # テンプレートのパスを指定
    success_url = reverse_lazy('success_url_name')  # 成功時のリダイレクト先URL

    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        name = json_data['name']
        start_date = json_data['start_date']
        end_date = json_data['end_date']
        timetables = json_data['timetables']
        selected_dates = json_data['selected_dates']

        interview = Interview.objects.create(name=name, start_date=start_date, end_date=end_date)

        for index, timetable in enumerate(timetables):
            key = index
            start_time = timetable['start_time']
            end_time = timetable['end_time']
            time_choice = TimeChoice.objects.create(key=key, stat_time=start_time, end_time=end_time)

        print(json_data)
