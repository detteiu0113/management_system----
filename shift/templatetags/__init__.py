from django import template

register = template.Library()

@register.simple_tag
def get_dynamic_attribute(obj, attr_prefix, index):
    """
    Retrieves the value of the dynamically generated attribute based on index.
    """
    try:
        attr_name = f"{attr_prefix}{index}"
        return getattr(obj, attr_name)
    except AttributeError:
        return None