from django.urls import path
from .views import TeacherDashboardView
from students.views import StudentNotableListView, StudentNotableCreateView, StudentNotableUpdateView, StudentNotableDeleteView, StudentSelectView, TeacherStudentListView
from report_card.views import ReportCardDetailView
from report.views import ReportListView, TeacherSubmitReportListView, SubmitVocabularyTestCreateView, SubmitReportUpdateView, SubmitReportCreateView
from vocabulary_test.views import VocabularyTestDetailView, VocabularyTestUpdateView
from test_result.views import TestResultDetailView
from special_lesson.views import SpecialLessonListView, SpecialLessonTeacherRequestFormView
from shift.views import ShiftDetailDisplayView, ShiftSelectView
from file.views import FileListView, FileDetailView
from year_schedule.views import  TeacherYearScheduleView
from accounts.views import ChangePasswordView, CustomUserProfileView

app_name = 'teacher'

urlpatterns = [
    path('', TeacherYearScheduleView.as_view(), name='dashboard'),

    path('account/', CustomUserProfileView.as_view(), name='account_profile'),
    path('account/change_password/', ChangePasswordView.as_view(), name='account_change_password'),

    path('submit_report/', TeacherSubmitReportListView.as_view(), name='submit_report_list'),
    path('submit_report/<int:pk>/', SubmitReportCreateView.as_view(), name='submit_report'),
    path('submit_report/<int:pk>/edit/', SubmitReportUpdateView.as_view(), name='submit_report_edit'),
    path('submit_report/vocabulary_test/', SubmitVocabularyTestCreateView.as_view(), name='submit_vocabulary_test'),

    path('student/', TeacherStudentListView.as_view(), name='document_list'),
    path('student/<int:pk>/', StudentSelectView.as_view(), name='document_select'),
    path('student/<int:pk>/notable/', StudentNotableListView.as_view(), name='student_notable_list'),
    path('student/<int:pk>/notable/create/', StudentNotableCreateView.as_view(), name='student_notable_create'),
    path('student/<int:pk>/notable/update/', StudentNotableUpdateView.as_view(), name='student_notable_update'),
    path('student/<int:pk>/notable/delete/', StudentNotableDeleteView.as_view(), name='student_notable_delete'),
    path('student/<int:pk>/test_result/', TestResultDetailView.as_view(), name='test_result_detail'),
    path('student/<int:pk>/report/', ReportListView.as_view(), name='report_detail'),
    path('student/<int:pk>/report_card/', ReportCardDetailView.as_view(), name='report_card_detail'), 
    path('student/<int:pk>/vocabulary_test/', VocabularyTestDetailView.as_view(), name='vocabulary_test_detail'),
    path('student/<int:pk>/vocabulary_test/update/', VocabularyTestUpdateView.as_view(), name='vocabulary_test_update'),

    path('shift/', ShiftSelectView.as_view(), name='shift_select'),
    path('shift/<int:year>/<int:week>/<int:day>/', ShiftDetailDisplayView.as_view(), name='shift_display'),

    path('special/', SpecialLessonListView.as_view(), name='special_lesson_list'),
    path('special/<int:pk>/', SpecialLessonTeacherRequestFormView.as_view(), name='special_lesson_request'),

    path('file/', FileListView.as_view(), name='file_list'),
    path('file/<int:pk>/', FileDetailView.as_view(), name='file_detail'),
]
