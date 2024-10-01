from django.urls import path
from .views import OwnerDashboardView
from accounts.views import CustomUserActivateView, CustomUserDeleteView, ChangePasswordView, CustomUserProfileView
from students.views import StudentNotableDeleteView, StudentNotableUpdateView, StudentNotableCreateView, StudentStatusUpdateView, StudentSelectView, OwnerStudentListView, OwnerStudentDetailView, OwnerStudentDetailUpdateView
from report_card.views import ReportCardDetailView, ReportCardUpdateView, BatchReportCardSelectView, BatchReportCardUpdateView
from regular_lesson.views import RegularLessonListView, RegularLessonCreateView, RegularLessonDeleteView, RegularLessonUpdateView, RegularLessonCancelView
from special_lesson.views import SpecialLessonCreateView, SpecialLessonListView, SpecialLessonDetailView, SpecialLessonAdminCreateView, SpecialLessonDeleteView, SpecialLessonAdminUpdateView, SpecialLessonAdminDeleteView, SpecialLessonPrintView
from shift.views import ShiftSelectView, ShiftTemplateView, ShiftTemplateUpdateView, ShiftDetailDisplayView, ShiftDetailView, ShiftDetailUpdateView, ShiftDetailReloadView, ShiftLessonCreateView, ShiftLessonDeleteView, ShiftTeacherShiftCreateView, ShiftTeacherShiftDeleteView, ShiftDeleteView
from report.views import OwnerSubmitReportListView, SubmitReportUpdateView, SubmitReportDeleteView, ReportListView
from vocabulary_test.views import VocabularyTestDetailView, VocabularyTestUpdateView
from test_result.views import AverageScoreListView, AverageScoreCreateView, TestResultDetailView, TestResultUpdateView, BatchTestResultUpdateView, AverageScoreUpdateView
from teacher_shift.views import FixedShiftListView, FixedShiftCreateView, SalaryPDFView, FixedShiftDeleteView, FixedShiftUpdateView, FixedShiftCancelView, SalaryCreateView, SalaryListView, SalaryUpdateView, SalaryDeleteView
from invoice.views import InvoicePDFView, InvoiceListView, InvoiceDeleteView, InvoiceUpdateView, PaidInvoiceListView, InvoiceCreateView
from year_schedule.views import OwnerYearScheduleView, EventCreateView, EventDeleteView, PrintMonthScheduleView, PrintSelectView
from file.views import OwnerFileListView, FileDetailView, FileDeleteView
from update_grade.views import UpdateStudentListView, UpdateStudentToMiddleView, UpdateStudentToHighView, UpdateStudentToGradView, UpdateShiftTemplateView, UpdateRegularLessonListView, UpdateFixedShiftListView, UpdateRegularLessonContinueView, UpdateFixedShiftDeleteView, UpdateFixedShiftUpdateView, UpdateFixedShiftContinueView, UpdateRegularLessonDeleteView, UpdateRegularLessonUpdateView
from teacher.views import TeacherListView, TeacherStatusUpdateView

app_name = 'owner'

urlpatterns = [
    path('', OwnerDashboardView.as_view(), name='dashboard'),

    path('account/', CustomUserProfileView.as_view(), name='account_profile'),
    path('account/change_password/', ChangePasswordView.as_view(), name='account_change_password'),

    path('<int:pk>/activate/', CustomUserActivateView.as_view(), name='user_activate'),
    path('<int:pk>/delete/', CustomUserDeleteView.as_view(), name='user_delete'),

    path('student/', OwnerStudentListView.as_view(), name='student_list'),
    path('student/<int:pk>', OwnerStudentDetailView.as_view(), name='student_detail'),
    path('student/<int:pk>/update', OwnerStudentDetailUpdateView.as_view(), name='student_detail_update'),

    path('student/<int:pk>/status', StudentStatusUpdateView.as_view(), name='student_status_update'),
    path('student/<int:pk>/notable/create/', StudentNotableCreateView.as_view(), name='student_notable_create'),
    path('student/<int:pk>/notable/update/', StudentNotableUpdateView.as_view(), name='student_notable_update'),
    path('student/<int:pk>/notable/delete/', StudentNotableDeleteView.as_view(), name='student_notable_delete'),

    path('student/<int:pk>/select/', StudentSelectView.as_view(), name='document_select'),
    path('student/<int:pk>/test_result/', TestResultDetailView.as_view(), name='test_result_detail'),
    path('student/<int:pk>/test_result/update/', TestResultUpdateView.as_view(), name='test_result_edit'),
    path('student/<int:pk>/report/', ReportListView.as_view(), name='report_detail'),
    path('student/<int:pk>/report_card/', ReportCardDetailView.as_view(), name='report_card_detail'), 
    path('student/<int:pk>/report_card/update/', ReportCardUpdateView.as_view(), name='report_card_edit'),
    path('student/<int:pk>/vocabulary_test/', VocabularyTestDetailView.as_view(), name='vocabulary_test_detail'),
    path('studnet/<int:pk>/vocabulary_test/update/', VocabularyTestUpdateView.as_view(), name='vocabulary_test_edit'),

    path('submit_report/', OwnerSubmitReportListView.as_view(), name='report_form_data'),
    path('submit_report/<int:pk>/edit/', SubmitReportUpdateView.as_view(), name='report_update'),
    path('submit_report/delete/', SubmitReportDeleteView.as_view(), name='report_delete_rows'),

    path('teacher/', TeacherListView.as_view(), name='teacher_list'),
    path('teacher/<int:pk>/status/', TeacherStatusUpdateView.as_view(), name='teacher_status_update'),

    path('regular/', RegularLessonListView.as_view(), name='regular_list'),
    path('regular/create/', RegularLessonCreateView.as_view(), name='regular_create'),
    path('regular/update/', RegularLessonUpdateView.as_view(), name='regular_update'),
    path('regular/<int:pk>/cancel', RegularLessonCancelView.as_view(), name='regular_cancel'),
    path('regular/<int:pk>/delete/', RegularLessonDeleteView.as_view(), name='regular_delete'),

    path('fixed_shift/', FixedShiftListView.as_view(), name='fixed_shift_list'),
    path('fixed_shift/create', FixedShiftCreateView.as_view(), name='fixed_shift_create'),
    path('fixed_shift/update/', FixedShiftUpdateView.as_view(), name='fixed_shift_update'),
    path('fixed_shift/<int:pk>/cancel/', FixedShiftCancelView.as_view(), name='fixed_shift_cancel'),
    path('fixed_shift/<int:pk>/delete/', FixedShiftDeleteView.as_view(), name='fixed_shift_delete'),

    path('special/', SpecialLessonListView.as_view(), name='special_list'),
    path('special/create/', SpecialLessonCreateView.as_view(), name='special_create'),
    path('special/<int:pk>/', SpecialLessonDetailView.as_view(), name='special_detail'),
    path('special/<int:pk>/print/', SpecialLessonPrintView.as_view(), name='special_print'),
    path('special/<int:pk>/delete/', SpecialLessonDeleteView.as_view(), name='special_delete'),
    path('special/admin/<int:pk>/update/', SpecialLessonAdminUpdateView.as_view(), name='special_admin_edit'),
    path('special/admin/<int:pk>/create/', SpecialLessonAdminCreateView.as_view(), name='special_admin_create'),
    path('special/admin/<int:pk>/delete/', SpecialLessonAdminDeleteView.as_view(), name='special_admin_delete'),

    path('shift/', ShiftSelectView.as_view(), name='shift_select'),
    path('shift/template/', ShiftTemplateView.as_view(), name='shift_template'),
    path('shift/temdplate/update/', ShiftTemplateUpdateView.as_view(), name='shift_template_update'),
    path('shift/detail/<int:year>/<int:week>/<int:day>/', ShiftDetailView.as_view(), name='shift_detail'),
    path('shift/detail/<int:year>/<int:week>/<int:day>/reload/', ShiftDetailReloadView.as_view(), name='shift_reload'),
    path('shift/detail/update/', ShiftDetailUpdateView.as_view(), name='shift_update'),
    path('shift/detail/lesson/create/', ShiftLessonCreateView.as_view(), name='shift_transfer_lesson'),
    path('shift/detail/lesson/delete/<int:lesson_pk>/<int:relation_num>/<int:unauthorized_absence>/', ShiftLessonDeleteView.as_view(), name='shift_absence_lesson'),
    path('shift/detail/tacher_shift/create/', ShiftTeacherShiftCreateView.as_view(), name='shift_teacher_add'),
    path('shift/detail/teacher_shift/delete/<int:teacher_shift_pk>/', ShiftTeacherShiftDeleteView.as_view(), name='shift_teacher_absence'),
    path('shift/detail/<int:year>/<int:week>/delete/', ShiftDeleteView.as_view(), name='shift_delete'),
    path('shift/detail/display/<int:year>/<int:week>/<int:day>/', ShiftDetailDisplayView.as_view(), name='shift_display'),

    path('salary/', SalaryListView.as_view(), name='salary_list'),
    path('salary/create/', SalaryCreateView.as_view(), name='salary_create'),
    path('salary/update/', SalaryUpdateView.as_view(), name='update_salary'),
    path('salary/delete/<int:pk>/', SalaryDeleteView.as_view(), name='delete_salary'),
    path('salary/pdf/', SalaryPDFView.as_view(), name='salary_show'),

    path('invoice/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoice/create/', InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoice/<int:pk>/delete/', InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoice/<int:pk>/update/', InvoiceUpdateView.as_view(), name='invoice_update'),
    
    path('invoice/pdf/', InvoicePDFView.as_view(), name='invoice_pdf'),

    path('paid_invoice/', PaidInvoiceListView.as_view(), name='paid_invoice'),

    path('test_result/', AverageScoreListView.as_view(), name='average_score_list'),
    path('test_result/create/', AverageScoreCreateView.as_view(), name='average_score_create'),
    path('test_result/<int:pk>/update/', AverageScoreUpdateView.as_view(), name='average_score_update'),
    path('test_result/<int:pk>/batch/update/', BatchTestResultUpdateView.as_view(), name='test_result_form'),

    path('report_card/', BatchReportCardSelectView.as_view(), name='report_card_semester'),
    path('report_card/<int:semester>/update/', BatchReportCardUpdateView.as_view(), name='report_card_form'),

    path('file/', OwnerFileListView.as_view(), name='file_list'),
    path('file/<int:pk>', FileDetailView.as_view(), name='file_detail'),
    path('file/<int:pk>/delete', FileDeleteView.as_view(), name='file_delete'),

    path('year_schedule/', OwnerYearScheduleView.as_view(), name='year_schedule_calendar'),
    path('year_schedule/add/', EventCreateView.as_view(), name='year_schedule_add'),
    path('year_schedule/delete/', EventDeleteView.as_view(), name='year_schedule_delete'),
    
    path('print/', PrintSelectView.as_view(), name='print_select'),
    path('print/<int:year>/<int:month>/', PrintMonthScheduleView.as_view(), name='print_month_schedule'),

    path('update/', UpdateStudentListView.as_view(), name='update_student_list'),
    path('update/<int:pk>/to_middle/', UpdateStudentToMiddleView.as_view(), name='update_to_middle'),
    path('update/<int:pk>/to_high/', UpdateStudentToHighView.as_view(), name='update_to_high'),
    path('update/<int:pk>/to_grad/', UpdateStudentToGradView.as_view(), name='update_to_grad'),
    path('update/regular/', UpdateRegularLessonListView.as_view(), name='update_regular_list'),
    path('update/regular/<int:pk>/continue/', UpdateRegularLessonContinueView.as_view(), name='update_regular_continue'),
    path('update/regular/<int:pk>/delete/', UpdateRegularLessonDeleteView.as_view(), name='update_regular_delete'),
    path('update/regular/update/', UpdateRegularLessonUpdateView.as_view(), name='update_regular_update'),
    path('update/shift/', UpdateFixedShiftListView.as_view(), name='update_shift_list'),
    path('update/shift/<int:pk>/continue/', UpdateFixedShiftContinueView.as_view(), name='update_shift_continue'),
    path('update/shift/<int:pk>/delete/', UpdateFixedShiftDeleteView.as_view(), name='update_shift_delete'),
    path('update/shift/update/', UpdateFixedShiftUpdateView.as_view(), name='update_shift_update'),
    path('update/shift_template/', UpdateShiftTemplateView.as_view(), name='update_shift_template'),
]
