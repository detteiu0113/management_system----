from django.db.models.query import QuerySet
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DeleteView
from django.http import Http404, FileResponse

from accounts.decorators import user_type_required
from .models import File

@method_decorator(user_type_required(), name='dispatch')
class OwnerFileListView(ListView):
    template_name = 'owner/file_list.html'
    model = File
    context_object_name = 'files'

    def get_queryset(self):
        queryset = super().get_queryset()
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')
        if month:
            try:
                month = int(month)
                queryset = queryset.filter(date__month=month)
            except ValueError:
                pass
        if year:
            try:
                year = int(year)
                queryset = queryset.filter(date__year=year)
            except ValueError:
                pass
        return queryset.order_by('-created_at')


@method_decorator(user_type_required(), name='dispatch')
class FileListView(ListView):
    model = File
    context_object_name = 'files'

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/file_list.html']

    def get_queryset(self):
        return File.objects.filter(accessible_users=self.request.user)
    
@method_decorator(user_type_required(), name='dispatch')
class FileDetailView(View):
    def get(self, request, pk, file_pk=None):
        # 保護者の場合のみ
        if request.user.is_parent:
            file_obj = File.objects.get(pk=file_pk)
        else:
            file_obj = File.objects.get(pk=pk)
        
        if not (request.user.is_owner or request.user in file_obj.accessible_users.all()):
            raise Http404("このファイルへのアクセス権限がありません。")
        
        return FileResponse(file_obj.file)

@method_decorator(user_type_required(), name='dispatch')
class FileDeleteView(DeleteView):
    template_name = 'owner/file_confirm_delete.html'
    model = File

    def get_success_url(self):
        return reverse_lazy('owner:file_list')