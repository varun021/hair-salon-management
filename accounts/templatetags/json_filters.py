from django import template
from django.core.serializers.json import DjangoJSONEncoder
import json

register = template.Library()

@register.filter(name='json')
def json_filter(value):
    """Convert a value to JSON string"""
    return json.dumps(value, cls=DjangoJSONEncoder) 