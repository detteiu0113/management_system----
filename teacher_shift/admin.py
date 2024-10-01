from django.contrib import admin
from .models import FixedShift, TemporalyShift, TeacherShift, Salary

admin.site.register(FixedShift)
admin.site.register(TemporalyShift)
admin.site.register(TeacherShift)
admin.site.register(Salary)