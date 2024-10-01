from datetime import timedelta, datetime, date, time
from collections import defaultdict
import json
import calendar
import os

from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, FormView, TemplateView, DeleteView, View
from django.urls import reverse_lazy
from django.db.models import Sum
from django.contrib import messages
from django.core.files.base import ContentFile
from django.conf import settings
from django.template.loader import render_to_string

from accounts.decorators import user_type_required
from accounts.models import CustomUser
from shift.models import ShiftTemplate
from teacher_shift.models import Salary
from year_schedule.models import Event
from .models import FixedShift, TeacherShift
from .forms import FixedShiftCreateForm, SalaryForm
from file.models import File
from utils.choices import TIME_CHOICES, DAY_CHOICES, SALARY_CHOICES, GRADE_CHOICES
from utils.mixins import FiscalYearMixin
from utils.helpers import generate_teacher_shifts, get_today, get_fiscal_year_boundaries
from utils.constants import hourly_teaching_allowance, hourly_administrative_allowance

from io import BytesIO
from xhtml2pdf import pisa

@method_decorator(user_type_required(), name='dispatch')
class FixedShiftListView(FiscalYearMixin, ListView):
    model = FixedShift
    context_object_name = 'fixed_shifts'
    template_name = 'owner/fixed_shift_list.html'

    def get_queryset(self):
        today = get_today()
        _, end_date = self.get_fiscal_year_boundaries(today)
        # order_byを追加(2024/5/5)
        return FixedShift.objects.filter(end_date=end_date).order_by('teacher', 'day', 'time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_choices_json'] = json.dumps(TIME_CHOICES)
        context['day_choices_json'] = json.dumps(DAY_CHOICES)
        return context   
        
@method_decorator(user_type_required(), name='dispatch')
class FixedShiftCreateView(FiscalYearMixin, CreateView):
    model = FixedShift
    form_class = FixedShiftCreateForm
    template_name = 'owner/fixed_shift_create.html'

    def get_initial(self):
        initial = super().get_initial()
        today = get_today()
        _, end_date = self.get_fiscal_year_boundaries(today)
        # 今日の日付をstart_dateの初期値として設定
        initial['start_date'] = today
        # 年度末の日付をend_dateの初期値として設定
        initial['end_date'] = end_date
        return initial

    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        pk = json_data['student']
        teacher = CustomUser.objects.get(pk=pk)
        start_date = datetime.strptime(json_data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(json_data['end_date'], '%Y-%m-%d').date()
        selected_timetable = json_data['selected_timetable']

        _, fiscal_end_date = get_fiscal_year_boundaries(start_date)

        # チェックを全て行うため2回書く必要あり
        for timetable in selected_timetable:
            day = int(timetable['day'])
            time = int(timetable['time'])

            if FixedShift.objects.filter(teacher=teacher, day=day, time=time, end_date=end_date).exists():
                get_day_display = DAY_CHOICES[day-1][1]
                get_time_display = TIME_CHOICES[time-1][1]
                return JsonResponse({'error': f'{get_day_display} {get_time_display}にはすでに授業が入っています。'})

        for timetable in selected_timetable:
            day = int(timetable['day'])
            time = int(timetable['time'])
            regular_lesson_admin = FixedShift.objects.create(
                teacher_id=pk,
                day=day,
                time=time,
                start_date=start_date,
                end_date=end_date
            )        

            generate_teacher_shifts(regular_lesson_admin, day, time, start_date, end_date)

        messages.success(request, "登録できました")
        
        return JsonResponse({'success':True,'redirect_url': self.get_success_url()})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grade_choices'] = GRADE_CHOICES
        context['time_choices_json'] = json.dumps(TIME_CHOICES)
        context['day_choices_json'] = json.dumps(DAY_CHOICES)      
        context['grade_choices_json'] = json.dumps(GRADE_CHOICES)
        return context
    
    def get_success_url(self):
        return reverse_lazy('owner:fixed_shift_list')
    
@method_decorator(user_type_required(), name='dispatch')
class FixedShiftUpdateView(FiscalYearMixin, View):
    def post(self, request, *args, **kwargs):
        recieved_json = request.POST.get('json_data')
        json_data = json.loads(recieved_json)
        id = json_data['shift_id']
        day = json_data['day']
        time = json_data['time']

        obj = FixedShift.objects.get(id=id)
        if obj.day == int(day) and obj.time == int(time):
            messages.error(request, '曜日と時間が変更されていません。')
            return JsonResponse({'error': True}, status=405)
        
        teacher = obj.teacher
        today = get_today()
        _, end_date = get_fiscal_year_boundaries(today)

        if FixedShift.objects.filter(teacher=teacher, day=day, time=time, end_date=end_date).exists():
            messages.error(self.request, 'すでに登録されているコマです。')
            return JsonResponse({'error': True}, status=405)

        # 今日以降のシフトを削除
        TeacherShift.objects.filter(date__gte=today, date__lte=end_date, fixed_shift=obj).delete()

        # ShiftTemplateから削除
        shift_template = ShiftTemplate.objects.get(fixed_shift=obj)
        shift_template.fixed_shift = None
        shift_template.save()

        # FixedShiftを本日で終了
        obj.end_date = today
        obj.save()

        # 新しいFiexedShiftを作成
        _, end_date = self.get_fiscal_year_boundaries(today)

        new_obj = FixedShift.objects.create(
            teacher=teacher,
            day=day,
            time=time,
            start_date=today,
            end_date=end_date
        )
        generate_teacher_shifts(new_obj, day, time, today, end_date)

        messages.success(request, "更新しました")
        
        return JsonResponse({"redirect_url": reverse_lazy('owner:fixed_shift_list')})
    
@method_decorator(user_type_required(), name='dispatch')
class FixedShiftDeleteView(DeleteView):
    model = FixedShift
    success_url = reverse_lazy('owner:fixed_shift_list')
    template_name = 'owner/fixed_shift_confirm_delete.html'

@method_decorator(user_type_required(), name='dispatch')
class FixedShiftCancelView(FiscalYearMixin, View):
    def post(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        fixed_shift = FixedShift.objects.get(pk=pk)

        # 今日以降のシフトを削除
        today = get_today()
        _, end_date = self.get_fiscal_year_boundaries(today)
        TeacherShift.objects.filter(date__gte=today, date__lte=end_date, fixed_shift=fixed_shift).delete()

        # ShiftTemplateから削除
        shift_template = ShiftTemplate.objects.get(fixed_shift=fixed_shift)
        shift_template.fixed_shift = None
        shift_template.save()

        # FIxedShiftを終了
        fixed_shift.end_date = today
        fixed_shift.save()

        messages.success(request, '中止できました')
        
        return HttpResponseRedirect(reverse_lazy('owner:fixed_shift_list'))

@method_decorator(user_type_required(), name='dispatch')
class SalaryPDFView(TemplateView):
    template_name = 'owner/salary_show.html'
    result_template_name = 'owner/salary_pdf.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teachers'] = CustomUser.objects.filter(is_teacher=True)
        return context
    
    def post(self, request, *args, **kwargs):
        year = int(request.POST.get('year'))
        month = int(request.POST.get('month'))
        teacher_id = request.POST.get('teacher_id')
        billing_date = request.POST.get('billing_date') or get_today()
        remarks = request.POST.get('remarks')
        start_date_of_month = date(year, month, 1)
        end_date_of_month = date(year, month, calendar.monthrange(year, month)[1])
        
        def publish_pdf(teacher_id):
            teacher = CustomUser.objects.get(id=teacher_id)
            _, end_date = get_fiscal_year_boundaries(start_date_of_month)

            price = TeacherShift.objects.filter(teacher=teacher, date__gte=start_date_of_month, date__lte=end_date_of_month).count() * hourly_teaching_allowance

            price = int(price)
            salaries = []
            total_salary = price
            class_salary, _ = Salary.objects.get_or_create(
                teacher=teacher,
                cost_name=0,
                date=end_date_of_month,
            )
            class_salary.price = price
            class_salary.save()
            salaries.append(class_salary)
            other_salaries = Salary.objects.filter(
                teacher=teacher,
                date__year=year,
                date__month=month,
            ).exclude(cost_name=0)
            for salary in other_salaries:
                salaries.append(salary)
                total_salary += salary.price

            context = {
                'year': year,
                'month': month,
                'teacher': teacher,
                'billing_date': billing_date,
                'salaries': salaries,
                'total_salary': total_salary,
                'remarks': remarks,
            }

            html_content = render_to_string('owner/salary_pdf.html', context)
            
            pdf_buffer = BytesIO()
            pisa.CreatePDF(html_content, dest=pdf_buffer)
            pdf_data = pdf_buffer.getvalue()
            pdf_buffer.close()

            file_name = f'{year}年{month}月_給与明細_{teacher.last_name}{teacher.first_name}様.pdf'
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
            file_obj.accessible_users.add(teacher)

            return pdf_data

        # 一人のみの作成
        if teacher_id:
            pdf_data = publish_pdf(teacher_id)
            teacher = CustomUser.objects.get(id=teacher_id)
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename={year}年{month}月_給与明細_{teacher.last_name}{teacher.first_name}様.pdf'
            return response

        # 全生徒の作成(休塾、退塾を除く)
        else:
            teachers = CustomUser.objects.filter(is_teacher=True, teacher_profile__is_withdrawn=False)
            for teacher in teachers:
                publish_pdf(teacher.id)
            messages.success(self.request, 'PDFの発行が完了しました。')
            return HttpResponseRedirect(reverse_lazy('owner:salary_show'))

@method_decorator(user_type_required(), name='dispatch')
class SalaryCreateView(FormView):
    template_name = 'owner/salary_form.html'
    form_class = SalaryForm
    success_url = reverse_lazy('owner:salary_list')

    def form_valid(self, form):
        form.save()
        messages.add_message(self.request, messages.SUCCESS, "登録できました")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['salary_choices_json'] = json.dumps(SALARY_CHOICES)
        context['hourly_rate'] = hourly_administrative_allowance
        return context

@method_decorator(user_type_required(), name='dispatch')
class SalaryListView(ListView):
    model = Salary
    template_name = 'owner/salary_list.html'

    def get_queryset(self):
        month = self.request.GET.get('month')
        teacher = self.request.GET.get('teacher')
        queryset = super().get_queryset()
        if teacher:
            queryset = queryset.filter(teacher__pk=teacher)
        if month:
            today = get_today()
            year = today.year
            month = int(month)
            start_date = date(year, month, 1)
            last_day = calendar.monthrange(year, month)
            end_date = date(year, month, last_day)
            queryset = queryset.filter(date__gte=start_date, date__lte=end_date)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teachers'] = CustomUser.objects.filter(is_teacher=True)
        teacher = self.request.GET.get('teacher')
        if teacher:
            teacher_salaries = Salary.objects.filter(teacher__pk=teacher).values('teacher').annotate(total_price=Sum('price'))
            context['teacher_salaries'] = teacher_salaries
        return context
    
@method_decorator(user_type_required(), name='dispatch')
class SalaryUpdateView(View):
    def post(self, request, *args, **kwargs):
        json_data = json.loads(request.POST.get('json_data'))
        salary_id = json_data['price_id']
        new_price = json_data['new_price']

        # 給与レコードを取得して価格を更新
        try:
            salary = Salary.objects.get(id=salary_id)
            salary.price = new_price
            salary.save()
            return JsonResponse({'success': True, 'redirect_url': reverse_lazy('owner:salary_list')})
        except Salary.DoesNotExist:
            return JsonResponse({'error': '指定された給与が見つかりませんでした。'}, status=404)

@method_decorator(user_type_required(), name='dispatch')
class SalaryDeleteView(View):
    def post(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        Salary.objects.get(pk=pk).delete()
        return HttpResponseRedirect(reverse_lazy('owner:salary_list'))