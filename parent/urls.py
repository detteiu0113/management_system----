from django.urls import path
from .views import ParentDashboardView, SwitchStudentView
from accounts.views import StudentSignUpView
from report_card.views import ReportCardDetailView
from report.views import ReportListView
from vocabulary_test.views import VocabularyTestDetailView
from test_result.views import TestResultDetailView
from regular_lesson.views import ParentLessonListView
from notification.views import NotificationListView
from special_lesson.views import SpecialLessonListView, SpecialLessonStudentRequestFormView
from year_schedule.views import ParentYearScheduleView
from file.views import FileDetailView, FileListView
from accounts.views import CustomUserProfileView, ChangePasswordView

app_name = 'parent'

urlpatterns = [
    # path('', ParentDashboardView.as_view(), name='dashboard'),

    path('account/', CustomUserProfileView.as_view(), name='account_profile'),
    path('account/change_password/', ChangePasswordView.as_view(), name='account_change_password'),

    path('test_result/', TestResultDetailView.as_view(), name='test_result_detail'),

    path('report/', ReportListView.as_view(), name='report_detail'),

    path('report_card/', ReportCardDetailView.as_view(), name='report_card_detail'), 

    path('vocabulary_test/', VocabularyTestDetailView.as_view(), name='vocabulary_test_detail'),

    path('switch_student/', SwitchStudentView.as_view(), name='switch_student'),

    path('notification/', NotificationListView.as_view(), name='notification_list'),

    path('lesson/', ParentLessonListView.as_view(), name='schedule_list'),

    path('year_schedule/', ParentYearScheduleView.as_view(), name='dashboard'),

    path('special/', SpecialLessonListView.as_view(), name='special_lesson_list'),
    path('special/<int:special_lesson_pk>/', SpecialLessonStudentRequestFormView.as_view(), name='special_lesson_request'),

    path('file/', FileListView.as_view(), name='file_list'),
    path('file/<int:file_pk>/', FileDetailView.as_view(), name='file_detail'),

    path('student_signup/', StudentSignUpView.as_view(), name='student_signup'),
]
