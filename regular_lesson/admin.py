from django.contrib import admin
from .models import RegularLessonAdmin, SpecialLessonAdmin, Lesson

admin.site.register(RegularLessonAdmin)
admin.site.register(SpecialLessonAdmin)

admin.site.register(Lesson)