from django import template
import decimal

register = template.Library()


@register.filter
def checked(value, querydict):
    events = querydict.getlist('events')
    teams = querydict.getlist('teams')
    meetings = querydict.getlist('meetings')

    if (str(value) in events) | (str(value) in teams) | (str(value) in meetings):
        return 'checked'
    return ''


@register.filter
def name(querydict):
    name_tmp = querydict.get('name')

    if name_tmp is None:
        return ''
    else:
        return name_tmp


@register.filter
def time_to_str(value):
    time = decimal.Decimal(value)
    time = time.quantize(decimal.Decimal('0.01'))

    if time >= 60.00:
        minutes = time // 60
        seconds = time - (minutes * 60)
        if seconds < 10.00:
            results = str(minutes) + ':0' + str(seconds)
        else:
            results = str(minutes) + ':' + str(seconds)
    else:
        results = str(time)
    return results


@register.filter
def time_disqualification(value):
    time = decimal.Decimal(value)
    time = time.quantize(decimal.Decimal('0.01'))

    if time >= 5000.00:
        return '記録なし'
    else:
        return time_to_str(value)
