from datetime import timedelta
import os

from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, FormView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect

from accounts.decorators import user_type_required
from accounts.models import CustomUser
from notification.models import Notification
from students.models import Student, StudentNotable
from utils.choices import GRADE_CHOICES
from utils.helpers import get_today

@method_decorator(user_type_required(), name='dispatch')
class OwnerDashboardView(ListView):
    template_name = 'owner/dashboard.html'
    model = Notification
    context_object_name = 'notifications'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['customusers'] = CustomUser.objects.filter(is_active=False)
        context['HOST_IP'] = os.environ.get('HOST_IP')
        return context

    def get_queryset(self):
        # 過去30日の通知を表示
        return Notification.objects.filter(user=self.request.user, created_at__gte=(get_today() - timedelta(days=30)))

    def post(self, request, *args, **kwargs):
        pk = request.POST.get('pk')
        notification = Notification.objects.get(pk=pk)
        notification.is_read = True
        notification.save()
        return HttpResponseRedirect(reverse_lazy('owner:dashboard'))