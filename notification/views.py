import json

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, View
from django.utils.decorators import method_decorator

from accounts.decorators import user_type_required
from .forms import NotificationForm
from .models import Notification
from accounts.models import CustomUser

@method_decorator(user_type_required(), name='dispatch')
class NotificationListView(ListView):
    model = Notification
    context_object_name = 'notifications'

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/notification_list.html']
    
    def get_queryset(self):
        queryset = Notification.objects.filter(is_read=False, user=self.request.user)

        is_read = self.request.GET.get('is_read')
        if is_read == 'true':
            queryset = queryset.filter(is_read=True)
        elif is_read == 'false':
            queryset = queryset.filter(is_read=False)

        return queryset.filter(user=self.request.user)
    
    def post(self, request, *args, **kwargs):
        notification_id = request.POST.get('notification_id')
        notification = Notification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()
        
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        if user_type == 'parent':
            return redirect(reverse('parent:notification_list', kwargs={'pk': self.request.user.parent_profile.current_student.pk}))
        elif user_type == 'teacher':
            return redirect(reverse('teacher:notification_list'))

# 未使用
def create_notification(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            send_to = form.cleaned_data['send_to']
            message = form.cleaned_data['message']
            is_priority = form.cleaned_data['is_priority']
            
            if send_to == 'teacher':
                users = CustomUser.objects.filter(is_teacher=True)
                
            elif send_to == 'parent':
                users = CustomUser.objects.filter(is_parent=True)
            else:
                users = CustomUser.objects.exclude(is_owner=True)
            
            for user in users:
                notification = Notification(user=user, message=message, is_priority=is_priority, sender=request.user)
                notification.save()
            
            return redirect('owner:notification_list')  # 通知一覧ページにリダイレクト
    else:
        form = NotificationForm()
    return render(request, 'owner/notification_create.html', {'form': form})

# 未使用
def notification_list(request):
    # ログインしているユーザーに関連する通知を取得
    sender = request.user
    notifications = Notification.objects.filter(sender=sender).order_by('-created_at')  # 最新の通知から表示する例

    return render(request, 'owner/dashboard.html', {'notifications': notifications})