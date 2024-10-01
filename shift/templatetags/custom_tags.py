from django import template

register = template.Library()

@register.simple_tag
def get_lesson(shift, lesson_number):
    lesson_key = f"lesson{lesson_number}"
    return getattr(shift.lessons, lesson_key, None)

