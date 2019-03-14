from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from pure_pagination import PaginationMixin
from .models import Record, Meeting, Team, Event


# Create your views here.
class RecordListView(PaginationMixin, ListView):
    model = Record
    paginate_by = 40

    def get_context_data(self, **kwargs):
        context = super(RecordListView, self).get_context_data(**kwargs)

        teams = Team.objects.all()
        meetings = Meeting.objects.all()
        events = Event.objects.all()
        context['teams'] = teams
        context['meetings'] = meetings
        context['events'] = events

        return context

    def get_queryset(self):
        results = self.model.objects.all()

        q_name = self.request.GET.get('name')
        q_events = self.request.GET.getlist('events')
        q_meetings = self.request.GET.getlist('meetings')
        q_teams = self.request.GET.getlist('teams')

        if len(q_events) != 0:
            results = results.filter(event_id__in=q_events)
        if len(q_meetings) != 0:
            results = results.filter(meeting_id__in=q_meetings)
        if len(q_teams) != 0:
            results = results.filter(swimmer__team__in=q_teams)

        if q_name is not None:
            results = results.filter(swimmer__name__contains=q_name)

        return results


class TestView(TemplateView):
    template_name = 'swimrecord/test.html'

    def get_context_data(self, **kwargs):
        context = super(TestView, self).get_context_data(**kwargs)
        context['hoge'] = 'fuga'
        return context
