from django.contrib import admin
from .models import TimeChoice,Interview,InterviewRequest




# Register your models here.
admin.site.register(InterviewRequest)
admin.site.register(Interview)
admin.site.register(TimeChoice)