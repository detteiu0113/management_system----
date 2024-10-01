from django.urls import path
from .views import TeacherSignUpView, ParentSignUpView
from django.contrib.auth.views import LogoutView, PasswordResetView, PasswordResetDoneView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
app_name = 'accounts'

urlpatterns = [
    path('logout/', LogoutView.as_view(), name='logout'),
    path('teacher_signup/', TeacherSignUpView.as_view(), name='teacher_signup'),
    path('parent_signup/', ParentSignUpView.as_view(), name='parent_signup'),
    path('password_reset/', PasswordResetView.as_view(
        email_template_name='accounts/password_reset_email.html',
        success_url = reverse_lazy("accounts:password_reset_done")
    ), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_change/', PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(), name='accounts_password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='accounts_password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        success_url = reverse_lazy("accounts:password_reset_complete")
    ), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]