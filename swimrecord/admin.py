from django.contrib import admin
from .models import Swimmer, Team, Record, Event, Meeting

# Register your models here.
admin.site.register(Meeting)
admin.site.register(Swimmer)
admin.site.register(Team)
admin.site.register(Record)
admin.site.register(Event)
