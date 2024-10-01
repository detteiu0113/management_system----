from django.utils.decorators import method_decorator
from django.views.generic import ListView, View, FormView, TemplateView, DetailView, UpdateView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse

from accounts.decorators import user_type_required
from .models import StudentNotable, Student
from .forms import StudentNotableForm, StudentStatusForm, StudentForm
from utils.choices import GRADE_CHOICES

@method_decorator(user_type_required(), name='dispatch') 
class StudentSelectView(TemplateView):
    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else 'teacher'
        return [f'{user_type}/document_select.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        pk = self.kwargs['pk']
        context['pk'] = pk
        student = Student.objects.get(pk=pk)
        context['student'] = student
        return context
    
@method_decorator(user_type_required(), name='dispatch')
class TeacherStudentListView(ListView):
    model = Student
    template_name = 'teacher/student_list.html'
    context_object_name = 'students'

    def get_queryset(self):
        # 休塾と退塾を含まない
        return Student.objects.filter(is_on_leave=False, is_withdrawn=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grades'] = [grade[1] for grade in GRADE_CHOICES]
        return context
    
@method_decorator(user_type_required('owner'), name='dispatch')
class OwnerStudentListView(ListView):
    model = Student
    template_name = 'owner/student_list.html'
    context_object_name = 'students'

    def get_queryset(self):
        # 休塾と退塾も含む
        return Student.objects.filter(parent__user__is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grades'] = [grade[1] for grade in GRADE_CHOICES]
        return context

@method_decorator(user_type_required(), name='dispatch')
class OwnerStudentDetailView(DetailView):
    model = Student
    template_name = 'owner/student_detail.html'
    context_object_name = 'student'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grades'] = [grade[1] for grade in GRADE_CHOICES]
        student = Student.objects.get(pk=self.kwargs['pk'])
        context['notables'] = StudentNotable.objects.filter(student=student)
        context['pk'] = student.pk
        return context
    

class OwnerStudentDetailUpdateView(UpdateView):
    model = Student
    template_name = 'owner/student_detail_update.html'
    form_class = StudentForm
    
    def get_success_url(self):
        return reverse_lazy('owner:student_detail', kwargs = {'pk': self.object.pk})

    def get_context_date(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pk'] = self.object.pk
        return context
 
@method_decorator(user_type_required(), name='dispatch')
class StudentNotableListView(ListView):
    model = StudentNotable
    context_object_name = 'notables'

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else 'teacher'
        return [f'{user_type}/student_notable_list.html']

    def get_queryset(self):
        pk = self.kwargs['pk']
        student = Student.objects.get(pk=pk)
        return StudentNotable.objects.filter(student=student)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = Student.objects.get(pk=self.kwargs['pk'])
        return context
    
@method_decorator(user_type_required(), name='dispatch')
class StudentNotableCreateView(CreateView):
    model = StudentNotable
    form_class = StudentNotableForm

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else 'teacher'
        return [f'{user_type}/student_notable_create.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = Student.objects.get(pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        form.instance.student = Student.objects.get(pk=self.kwargs['pk'])
        form.instance.writer = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        user_type = 'owner' if self.request.user.is_owner else 'teacher'
        student_id = self.kwargs['pk']
        if user_type == 'teacher':
            return reverse_lazy('teacher:student_notable_list', kwargs={'pk': student_id})
        else:
            return reverse_lazy('owner:student_detail', kwargs={'pk': student_id})
    
@method_decorator(user_type_required(), name='dispatch')
class StudentNotableUpdateView(UpdateView):
    model = StudentNotable
    form_class = StudentNotableForm

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else 'teacher'
        return [f'{user_type}/student_notable_update.html']
    
    def get_success_url(self):
        student_id = self.object.student.id
        user_type = 'owner' if self.request.user.is_owner else 'teacher'
        if user_type == 'teacher':
            return reverse_lazy('teacher:student_notable_list', kwargs={'pk': student_id})
        else:
            return reverse_lazy('owner:student_detail', kwargs={'pk': student_id})        
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = Student.objects.get(pk=self.object.student.id)
        return context
    
@method_decorator(user_type_required(), name='dispatch')
class StudentNotableDeleteView(View):
    def post(self, request, *args, **kwargs):
        user_type = 'owner' if request.user.is_owner else 'teacher'
        pk = self.kwargs['pk']
        obj = StudentNotable.objects.get(pk=pk)
        student_id = obj.student.id
        obj.delete()
        if user_type == 'teacher':
            return HttpResponseRedirect(reverse_lazy('teacher:student_notable_list', kwargs={'pk': student_id}))
        else:
            return HttpResponseRedirect(reverse_lazy('owner:student_detail', kwargs={'pk': student_id}))
    
@method_decorator(user_type_required(), name='dispatch')
class StudentStatusUpdateView(FormView):
    template_name = 'owner/student_status_update.html'
    form_class = StudentStatusForm

    def get_success_url(self):
        return reverse_lazy('owner:student_detail', kwargs={'pk': self.kwargs['pk']})  # ここは適切なURLに変更してください
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student'] = Student.objects.get(pk=self.kwargs['pk'])
        return context

    def get_initial(self):
        student = Student.objects.get(pk=self.kwargs['pk'])
        current_status = ''
        if student.is_on_leave:
            current_status = 'on_leave'
        elif student.is_withdrawn:
            current_status = 'withdrawn'
        elif student.is_planning_to_withdraw:
            current_status = 'planning_to_withdraw'
        return {'status': current_status}

    def form_valid(self, form):
        student = Student.objects.get(pk=self.kwargs['pk'])

        # フォームから新しいステータスを取得
        new_status = form.cleaned_data['status']
        
        # すべてのステータスを初期化
        student.is_on_leave = False
        student.is_withdrawn = False
        student.is_planning_to_withdraw = False

        # 新しいステータスに基づいて、適切なフィールドを True に設定
        if new_status == 'on_leave':
            student.is_on_leave = True
        elif new_status == 'withdrawn':
            student.is_withdrawn = True
        elif new_status == 'planning_to_withdraw':
            student.is_planning_to_withdraw = True
        
        # データベースに変更を保存
        student.save()
        return super().form_valid(form)