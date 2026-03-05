from django import template

register = template.Library()

@register.filter
def intcomma(value):
    """
    Converts an integer to a string containing commas every three digits.
    For example: 3000 becomes '3,000' and 45000000 becomes '45,000,000'.
    """
    if value is None:
        return '0'
    
    try:
        value = int(value)
    except (ValueError, TypeError):
        return str(value)
    
    s = str(value)
    if len(s) <= 3:
        return s
    else:
        groups = []
        while s:
            groups.append(s[-3:])
            s = s[:-3]
        return ','.join(reversed(groups))
