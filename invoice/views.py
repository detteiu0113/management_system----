from datetime import date, timedelta
import os
import calendar
import json
from io import BytesIO

from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView, View, UpdateView
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.db.models import Q, Sum
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.conf import settings

from .models import Invoice, PaidInvoice
from .forms import InvoiceForm
from accounts.decorators import user_type_required
from accounts.models import CustomUser
from students.models import Student
from file.models import File
from regular_lesson.models import RegularLessonAdmin, Lesson
from year_schedule.models import Event
from utils.choices import GRADE_CHOICES, DAY_CHOICES
from utils.constants import price_settings
from utils.helpers import get_fiscal_year_boundaries, get_today

from xhtml2pdf import pisa

@method_decorator(user_type_required(), name='dispatch')
class InvoiceListView(ListView):
    model = Invoice
    template_name = 'owner/invoice_list.html'  # 使用するテンプレートの指定
    context_object_name = 'invoices'

    def get_queryset(self):
        queryset = super().get_queryset()
        today = get_today()
        year = self.request.GET.get('year') or today.year
        month = self.request.GET.get('month') or today.month
        student_id = self.request.GET.get('student_id')
        year = int(year)
        month = int(month)
        start_date = date(year, month, 1)
        end_date = date(year, month, calendar.monthrange(year, month)[1])
        queryset = queryset.filter(date__gte=start_date, date__lte=end_date)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        return queryset.order_by('student__grade', 'student', 'date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Student.objects.all()
        today = get_today()
        context['years'] = range(today.year - 3, today.year + 4)
        context['months'] = range(1, 13)
        year = self.request.GET.get('year') or today.year
        month = self.request.GET.get('month') or today.month
        year = int(year)
        month = int(month)
        context['selected_year'] = year
        context['selected_month'] = month
        return context
    
    def post(self, request, *args, **kwargs):
        # POSTリクエストから削除対象の請求書IDを取得
        invoice_id = request.POST.get('delete_invoice_id')
        if invoice_id:
            # 請求書を削除
            try:
                invoice = Invoice.objects.get(id=invoice_id)
                invoice.delete()
            except Invoice.DoesNotExist:
                pass
            # 削除後にリダイレクト
            return redirect('owner:invoice_list', pk=self.kwargs['pk'])
        # 削除対象がない場合は通常のGETリクエストの処理を継続

        messages.success(request, '編集できました')

        return super().get(request, *args, **kwargs)
    
@method_decorator(user_type_required(), name='dispatch')
class InvoiceCreateView(ListView):
    model = Student
    template_name = 'owner/invoice_student_list.html'
    context_object_name = 'students'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grades'] = GRADE_CHOICES
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search_query')
        if search_query:
            queryset = queryset.filter(Q(last_name__icontains=search_query) | Q(first_name__icontains=search_query))
        return queryset

    def post(self, request, *args, **kwargs):

        # POSTリクエストからデータを取得
        data = json.loads(request.body)
        cost_name = data.get('costName')
        price = data.get('price')
        date = data.get('date')
        selected_students = data.get('selectedStudents')
        for student_id in selected_students:
            Invoice.objects.create(student_id=student_id ,cost_name=cost_name, price=price, date=date)
        messages.success(request, "保存しました")
            
        return JsonResponse({'redirect_url': reverse_lazy('owner:invoice_create')})

"""
@method_decorator(user_type_required(), name='dispatch') 
class InvoiceCreateView(TemplateView):
    template_name = 'owner/invoice_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['form'] = InvoiceForm
        context['pk'] = self.kwargs['pk']
        return context

    def post(self, request, *args, **kwargs):
        student_id = self.kwargs['pk']
        cost_name = request.POST.get('cost_name')
        price = request.POST.get('price')
        date = request.POST.get('date')
        Invoice.objects.create(
            student_id=student_id,
            cost_name=cost_name,
            price=price,
            date=date,
        )
        return HttpResponseRedirect(reverse_lazy('owner:invoice_list', kwargs={'pk': student_id}))
"""

@method_decorator(user_type_required(), name='dispatch')
class InvoiceUpdateView(UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'owner/invoice_update.html'

    def get_success_url(self):
        return reverse_lazy('owner:invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pk'] = self.kwargs['pk']
        context['student'] = self.get_object().student
        return context
    
@method_decorator(user_type_required(), name='dispatch')
class InvoiceDeleteView(View):
    def post(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        invoice = Invoice.objects.get(pk=pk)
        invoice.delete()
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('owner:invoice_list')

@method_decorator(user_type_required(), name='dispatch')
class InvoicePDFView(TemplateView):
    model=Invoice
    template_name='owner/invoice_form.html'
    result_template_name = 'owner/invoice_pdf.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Student.objects.all()
        return context
    
    def post(self, request, *args, **kwargs):
        year = int(request.POST.get('year'))
        month = int(request.POST.get('month'))
        student_id = request.POST.get('student_id')
        billing_date = request.POST.get('billing_date') or get_today()
        remarks = request.POST.get('remarks')
        start_date_of_month = date(year, month, 1)
        end_date_of_month = date(year, month, calendar.monthrange(year, month)[1])
        
        def publish_pdf(student_id):
            student = Student.objects.get(id=student_id)
            grade = student.grade
            # 日割りの計算用
            price_rate = None
            _, end_date = get_fiscal_year_boundaries(start_date_of_month)

            # 今月から始まったRegularLessonAdminが存在する場合(尚且つ終了日が年度末)
            if RegularLessonAdmin.objects.filter(student=student, start_date__gte=start_date_of_month, end_date=end_date).exists():

                # 各曜日の授業数
                weekday_lessons = [RegularLessonAdmin.objects.filter(student=student, day=day[0], end_date=end_date).count() for day in DAY_CHOICES]

                # 全て授業があった場合の授業数
                full_lesson_count = 0

                current_date = start_date_of_month
                while current_date <= end_date_of_month:
                    # 休校日でない場合のみ計算
                    if not Event.objects.filter(date=current_date, is_closure=True).exists():
                        weekday = current_date.weekday() # 0が日曜日,1が月曜日,6が土曜日
                    
                        # 月曜日から金曜日までのみ計算
                        if DAY_CHOICES[0][0] <= int(weekday) <= DAY_CHOICES[-1][0]:
                            full_lesson_count += weekday_lessons[weekday-1]
                            
                        current_date += timedelta(days=1)

                actual_lesson_count = Lesson.objects.filter(
                    Q(student=student, date__gte=start_date_of_month, date__lte=end_date_of_month, is_regular=True) or Q(student=student, date__gte=start_date_of_month, date__lte=end_date_of_month, is_temporaly=True)
                ).count()

                price_rate = actual_lesson_count / full_lesson_count

            # 週に受ける授業の回数を計算
            lessons_per_week = min(RegularLessonAdmin.objects.filter(student=student, end_date=end_date).count(), 5)
            if lessons_per_week:
                base_price = price_settings[grade][lessons_per_week]
            else:
                base_price = 0

            if not price_rate:
                price = base_price
            else:
                price = base_price * price_rate
            
            # 合計を計算
            price = int(price)
            invoices = []
            total_price = price
            lesson_invoice, _ = Invoice.objects.get_or_create(
                student=student,
                cost_name='授業料',
                date=end_date_of_month,
            )
            lesson_invoice.price = price
            lesson_invoice.save()
            invoices.append(lesson_invoice)
            other_invoices = Invoice.objects.filter(
                student=student,
                date__year=year,
                date__month=month,
            ).exclude(cost_name='授業料')
            for invoice in other_invoices:
                invoices.append(invoice)
                total_price += invoice.price

            # 振り込み完了か確認
            parent = student.parent.all()[0].user
            if month == 1:  # 現在が1月の場合、前の月は前年の12月
                previous_year = year - 1
                previous_month = 12
            else:
                previous_year = year
                previous_month = month - 1
            try:
                # PaidInvoiceオブジェクトが存在している場合のみTrue
                bank_info = PaidInvoice.objects.get(parent=parent, date__year=previous_year, date__month=previous_month)
            except ObjectDoesNotExist:
                bank_info = False

            context = {
                'year': year,
                'month': month,
                'student': student,
                'billing_date': billing_date,
                'invoices': invoices,
                'price': price,
                'total_price': total_price,
                'remarks': remarks,
                'bank_info': bank_info,
            }

            html_content = render_to_string('owner/invoice_pdf.html', context)
            
            pdf_buffer = BytesIO()
            pisa.CreatePDF(html_content, dest=pdf_buffer)
            pdf_data = pdf_buffer.getvalue()
            pdf_buffer.close()

            file_name = f'{year}年{month}月_請求書_{student.last_name}{student.first_name}様.pdf'
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)

            # ファイルが存在する場合は削除
            if os.path.exists(file_path):
                os.remove(file_path)

            file_obj, created = File.objects.get_or_create(file=file_name, date=date(year, month, 1))
            file_obj.file.save(file_name, ContentFile(pdf_data), save=True)
            if not created:
                file_obj.created_at = get_today()
                file_obj.save()

            # アクセス可能なユーザーを追加
            file_obj.accessible_users.add(student.parent.all()[0].user)

            return pdf_data

        # 一人のみの作成
        if student_id:
            pdf_data = publish_pdf(student_id)
            student = Student.objects.get(id=student_id)
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename={year}年{month}月_請求書_{student.last_name}{student.first_name}様.pdf'
            return response

        # 全生徒の作成(休塾、退塾を除く)
        else:
            students = Student.objects.filter(is_on_leave=False, is_withdrawn=False)
            for student in students:
                publish_pdf(student.id)
            messages.success(self.request, 'PDFの発行が完了しました。')
            return HttpResponseRedirect(reverse_lazy('owner:invoice_pdf'))

@method_decorator(user_type_required(), name='dispatch')
class PaidInvoiceListView(ListView):
    model = PaidInvoice  # リスト表示するモデル
    template_name = 'owner/paid_invoice.html'
    context_object_name = 'paid_invoices'
    queryset = PaidInvoice.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        month = self.request.GET.get('month')
        today = get_today()
        if not PaidInvoice.objects.filter(date__year=today.year, date__month=today.month).exists():
            first_date = date(today.year, today.month, 1)
            parents = CustomUser.objects.filter(is_parent=True)
            for parent in parents:
                PaidInvoice.objects.create(date=first_date, parent=parent)
            queryset = PaidInvoice.objects.all()
        if month:
            queryset = queryset.filter(date__month=month)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['parents'] = CustomUser.objects.filter(is_parent=True)
        return context
    
    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        data_id = json_data['user_id']
        is_paid = json_data['is_paid']
        obj = PaidInvoice.objects.get(id=data_id)
        obj.is_paid = is_paid
        obj.save()
        return JsonResponse({'success': True})

