from django.contrib.auth.views import LoginView
from django.forms import BaseModelForm
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import View, DeleteView, ListView, FormView, TemplateView
from django.views.generic.edit import CreateView
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.contrib import messages 
from django.contrib.auth.views import PasswordChangeView, PasswordResetView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.messages.views import SuccessMessageMixin

from .models import OwnerProfile, TeacherProfile, CustomUser
from .forms import CustomUserLoginForm, OwnerCreationForm, TeacherCreationForm, ParentCreationForm, StudentCreationForm, TeacherStatusForm
from .decorators import user_type_required
from students.models import Student
from accounts.models import OwnerProfile, TeacherProfile, ParentProfile
from report_card.models import ReportGrade, SEMESTER_CHOICES
from report_card.models import SUBJECT_CHOICES as REPORT_SUBJECT_CHOICES
from vocabulary_test.models import TestResult, CATEGORY_CHOICES, PROGRAM_CHOICES, COUNT_CHOICES

class CustomUserLoginView(LoginView):
    form_class = CustomUserLoginForm
    template_name = 'accounts/login.html'
    # ログイン時にリダイレクト(開発中はFalse)
    # redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.is_authenticated:
            if self.request.user.is_owner:
                return redirect('owner:dashboard')
            elif self.request.user.is_parent:
                pk = self.request.user.parent_profile.current_student.pk
                return redirect('parent:dashboard', pk)
            elif self.request.user.is_teacher:
                return redirect('teacher:dashboard')
        return response
    
class TeacherSignUpView(CreateView):
    form_class = TeacherCreationForm 
    template_name = 'accounts/teacher_signup.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        with transaction.atomic():
            teacher = form.save(commit=False)
            teacher.email = form.cleaned_data['username']
            teacher.is_teacher = True
            teacher.is_active = False
            teacher.save()

            # プロファイルの作成
            TeacherProfile.objects.create(user=teacher)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('login') 

class ParentSignUpView(CreateView):
    form_class = ParentCreationForm
    template_name = 'accounts/parent_signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        with transaction.atomic():
            parent = form.save(commit=False)
            parent.email = form.cleaned_data['username']
            parent.is_parent = True
            parent.is_active = False
            parent.save()

            # プロファイルの作成
            parent_profile = ParentProfile.objects.create(user=parent)

            student_last_name = form.cleaned_data['student_last_name']
            student_first_name = form.cleaned_data['student_first_name']
            birth_date = form.cleaned_data['student_birth_date']
            student_elementary_school = form.cleaned_data['student_elementary_school']
            student_school = form.cleaned_data['student_school']
            student_high_school = form.cleaned_data['student_high_school']

            student = Student.objects.create(
                last_name=student_last_name,
                first_name=student_first_name,
                birth_date=birth_date,
                elementary_school=student_elementary_school,
                school=student_school,
                high_school=student_high_school,
            )
            student.update_grade()
            parent_profile.student.add(student)
            parent_profile.current_student = student
            parent_profile.save()

            semester_choices = [semester[0] for semester in SEMESTER_CHOICES]
            subject_choices = [subject[0] for subject in REPORT_SUBJECT_CHOICES]

            for semester in semester_choices:
                for subject in subject_choices:
                    ReportGrade.objects.create(
                        student=student,
                        semester=semester,
                        subject=subject,
                    )

            category_choices = [category[0] for category in CATEGORY_CHOICES]
            program_choices = [program[0] for program in PROGRAM_CHOICES]
            count_choices = [count[0] for count in COUNT_CHOICES]

            for category in category_choices:
                for program in program_choices:
                    for count in count_choices:
                        TestResult.objects.create(
                            student=student,
                            category=category,
                            program=program,
                            count=count,
                        )
            cleaned_data = form.cleaned_data
            print(cleaned_data)

        return super().form_valid(form)
    
    def form_invalid(self, form):
        form.fields['student_school'].initial = form.cleaned_data.get('student_school', None)
        return super().form_invalid(form)

@method_decorator(user_type_required(), name='dispatch')
class StudentSignUpView(CreateView):
    form_class = StudentCreationForm
    template_name = 'parent/student_signup.html'

    def form_valid(self, form):
        parent = self.request.user
        parent_profile = ParentProfile.objects.get(user=parent)

        form.save()

        student = form.instance
        student.update_grade()
        parent_profile.student.add(student)
        # ログイン保持のためここを変更
        # parent_profile.current_student = student
        parent_profile.save()

        semester_choices = [semester[0] for semester in SEMESTER_CHOICES]
        subject_choices = [subject[0] for subject in REPORT_SUBJECT_CHOICES]

        for semester in semester_choices:
            for subject in subject_choices:
                ReportGrade.objects.create(
                    student=student,
                    semester=semester,
                    subject=subject,
                )

        category_choices = [category[0] for category in CATEGORY_CHOICES]
        program_choices = [program[0] for program in PROGRAM_CHOICES]
        count_choices = [count[0] for count in COUNT_CHOICES]

        for category in category_choices:
            for program in program_choices:
                for count in count_choices:
                    TestResult.objects.create(
                        student=student,
                        category=category,
                        program=program,
                        count=count,
                    )

        messages.success(self.request, '送信しました')

        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('parent:dashboard', kwargs={'pk': self.kwargs['pk']})
    
@method_decorator(user_type_required(), name='dispatch')
class CustomUserProfileView(TemplateView):
    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/account_profile.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
    
@method_decorator(user_type_required(), name='dispatch')
class ChangePasswordView(PasswordChangeView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy('login')

    def get_template_names(self):
        user_type = 'owner' if self.request.user.is_owner else ('teacher' if self.request.user.is_teacher else 'parent')
        return [f'{user_type}/account_change_password.html']
    


@method_decorator(user_type_required(), name='dispatch')
class CustomUserActivateView(View):
    def post(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        user = CustomUser.objects.get(pk=pk)
        user.is_active = True
        user.save()
        return HttpResponseRedirect(reverse_lazy('owner:dashboard'))

@method_decorator(user_type_required(), name='dispatch')
class CustomUserDeleteView(DeleteView):
    model = CustomUser
    success_url = reverse_lazy('owner:dashboard')
    template_name = 'owner/user_confirm_delete.html'

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.is_parent:
            student = obj.parent_profile.current_student
            student.delete()
        return super().post(request, *args, **kwargs)
