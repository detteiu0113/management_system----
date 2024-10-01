from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, FormView
from django.urls import reverse_lazy

from accounts.decorators import user_type_required
from students.models import Student
from notification.models import Notification
from utils.choices import GRADE_CHOICES
from accounts.models import CustomUser
from accounts.forms import TeacherStatusForm

# 未使用
@method_decorator(user_type_required(), name='dispatch')
class TeacherDashboardView(TemplateView):
    template_name = 'teacher/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications = Notification.objects.filter(user=self.request.user)  # すべての通知を取得
        context['notifications'] = notifications  # テンプレートコンテキストに通知データを追加
        return context
    

@method_decorator(user_type_required('owner'), name='dispatch')
class TeacherListView(ListView):
    model = CustomUser
    template_name = 'owner/teacher_list.html'
    context_object_name = 'teachers'

    def get_queryset(self):
        return CustomUser.objects.filter(is_teacher=True, is_active=True)

@method_decorator(user_type_required('owner'), name='dispatch')
class TeacherStatusUpdateView(FormView):
    template_name = 'owner/teacher_status_update.html'
    form_class = TeacherStatusForm

    def get_success_url(self):
        return reverse_lazy('owner:teacher_list')

    def get_initial(self):
        teacher = CustomUser.objects.get(pk=self.kwargs['pk'])
        profile = teacher.teacher_profile
        current_status = ''
        if profile.is_withdrawn:
            current_status = 'withdrawn'
        return {'status': current_status}

    def form_valid(self, form):
        teacher = CustomUser.objects.get(pk=self.kwargs['pk'])

        profile = teacher.teacher_profile
        # フォームから新しいステータスを取得
        new_status = form.cleaned_data['status']
        profile.is_withdrawn = False

        if new_status == 'withdrawn':
            profile.is_withdrawn = True
        
        # データベースに変更を保存
        profile.save()
        return super().form_valid(form)