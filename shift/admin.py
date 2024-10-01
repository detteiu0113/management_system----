from django.contrib import admin
from .models import ShiftTemplateLessonRelation, ShiftTemplate, ShiftLessonRelation, Shift

admin.site.register(ShiftTemplateLessonRelation)
admin.site.register(ShiftTemplate)
admin.site.register(ShiftLessonRelation)
admin.site.register(Shift)