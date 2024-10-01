from django.contrib import admin
from .models import SpecialLesson, SpecialLessonStudentRequest, SpecialLessonTeacherRequest

# Register your models here.
admin.site.register(SpecialLesson)
admin.site.register(SpecialLessonStudentRequest)
admin.site.register(SpecialLessonTeacherRequest)