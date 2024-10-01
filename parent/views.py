from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView

from accounts.decorators import user_type_required
from .forms import SwitchStudentForm
from accounts.models import ParentProfile

@method_decorator(user_type_required(), name='dispatch')
class ParentDashboardView(TemplateView):
    template_name = 'parent/dashboard.html'

@method_decorator(user_type_required(), name='dispatch')
class SwitchStudentView(FormView):
    template_name = 'parent/switch_student.html'
    form_class = SwitchStudentForm
    
    def get_form_kwargs(self):
        kwargs = super(SwitchStudentView, self).get_form_kwargs()
        kwargs['parent_profile'] = ParentProfile.objects.get(user=self.request.user)
        return kwargs

    def form_valid(self, form):
        student_id = form.cleaned_data['student'].id
        parent_profile = ParentProfile.objects.get(user=self.request.user)
        parent_profile.current_student_id = student_id
        parent_profile.save()
        self.student_id = student_id
        return super(SwitchStudentView, self).form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('parent:dashboard', kwargs={'pk': self.student_id})