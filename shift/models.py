from django.db import models
from regular_lesson.models import Lesson, RegularLessonAdmin
from teacher_shift.models import FixedShift, TeacherShift
from utils.choices import DAY_CHOICES, TIME_CHOICES, ROOM_CHOICES, SPECIAL_TIME_CHOICES

class ShiftTemplateLessonRelation(models.Model):
    # 意味合い的にはOneToOneFieldでいいが、ドラッグ&ドロップの時に重複するためForeignKeyを設定
    template_lesson1 = models.ForeignKey(RegularLessonAdmin, on_delete=models.SET_NULL, blank=True, null=True, related_name='template_lesson1')
    template_lesson2 = models.ForeignKey(RegularLessonAdmin, on_delete=models.SET_NULL, blank=True, null=True, related_name='template_lesson2')
    template_lesson3 = models.ForeignKey(RegularLessonAdmin, on_delete=models.SET_NULL, blank=True, null=True, related_name='template_lesson3')
    template_lesson4 = models.ForeignKey(RegularLessonAdmin, on_delete=models.SET_NULL, blank=True, null=True, related_name='template_lesson4')

    def __str__(self):
        return f'{self.template_lesson1} - {self.template_lesson2} - {self.template_lesson3} - {self.template_lesson4}'

class ShiftTemplate(models.Model):
    fixed_shift = models.ForeignKey(FixedShift, on_delete=models.SET_NULL, blank=True, null=True)
    day = models.IntegerField(choices=DAY_CHOICES)
    time = models.IntegerField(choices=TIME_CHOICES)
    room = models.IntegerField(choices=ROOM_CHOICES, blank=True, null=True)
    lessons = models.OneToOneField(ShiftTemplateLessonRelation, on_delete=models.SET_NULL, blank=True, null=True, related_name='template_lessons')
    is_next_year = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.fixed_shift} - {self.lessons}'
    
# 何かに使ってるはず
RegularLessonAdmin.shift_templates = models.ManyToManyField(
    ShiftTemplate,
    through='ShiftTemplateLessonRelation',
    related_name='regular_lesson_admins'
)

class ShiftLessonRelation(models.Model):
    lesson1 = models.ForeignKey(Lesson, on_delete=models.SET_NULL, blank=True, null=True, related_name='lesson1')
    lesson2 = models.ForeignKey(Lesson, on_delete=models.SET_NULL, blank=True, null=True, related_name='lesson2')
    lesson3 = models.ForeignKey(Lesson, on_delete=models.SET_NULL, blank=True, null=True, related_name='lesson3')
    lesson4 = models.ForeignKey(Lesson, on_delete=models.SET_NULL, blank=True, null=True, related_name='lesson4')

    def __str__(self):
        return f'{self.lesson1} - {self.lesson2} - {self.lesson3} - {self.lesson4}'

class Shift(models.Model):
    teacher_shift = models.ForeignKey(TeacherShift, on_delete=models.SET_NULL, blank=True, null=True, related_name='teacher_shift')
    date = models.DateField(blank=True, null=True)
    time = models.IntegerField(choices=SPECIAL_TIME_CHOICES+TIME_CHOICES, blank=True, null=True)
    room = models.IntegerField(choices=ROOM_CHOICES, blank=True, null=True)
    lessons = models.OneToOneField(ShiftLessonRelation, on_delete=models.CASCADE, blank=True, null=True, related_name='lessons')

    def __str__(self):
        return f'{self.teacher_shift} - {self.date} - {self.get_time_display()} - {self.get_room_display()} - {self.lessons}'