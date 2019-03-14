from django.views.generic import TemplateView, ListView, DetailView
from pure_pagination import PaginationMixin
from django.db import models
from .models import Record, Meeting, Team, Event, Swimmer
from statistics import mean, stdev
from decimal import Decimal


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


class SwimmerDetailView(DetailView):
    model = Swimmer
    records = Record.objects.filter(record__lt=5000)
    events = Event.objects.all()

    def get_context_data(self, **kwargs):
        context = super(SwimmerDetailView, self).get_context_data(**kwargs)

        data = {}
        data['long'] = self.__get_data(is_long=True, swimmer_pk=context['swimmer'].pk)
        data['short'] = self.__get_data(is_long=False, swimmer_pk=context['swimmer'].pk)

        history = self.records.filter(swimmer__pk=context['swimmer'].pk).order_by('meeting__date')

        context['history'] = history
        context['data'] = data

        return context

    def __get_data(self, is_long, swimmer_pk):
        data = []
        for event in self.events:
            best = self.records.filter(event__pk=event.pk).filter(meeting__is_long=is_long)
            best = best.filter(swimmer__pk=swimmer_pk).order_by('record').first()

            if best is None:
                continue
            else:
                ranking = self.records.filter(event__pk=event.pk).filter(meeting__is_long=is_long)
                ranking = ranking.values('swimmer__name').annotate(models.Min('record'))
                ranking = ranking.values_list('record__min')
                deviation = self.__get_deviation(ranking, best)
                data.append({'best': best, 'deviation': deviation})
        return data

    # rankingはstr型の記録のリスト
    # recordもstr型の記録
    @staticmethod
    def __get_deviation(ranking, record):
        ranking = list(map((lambda x: float(x[0])), ranking))
        avg = mean(ranking)
        std_ev = stdev(ranking)

        deviation = 50.0 - ((float(record.record) - avg) / std_ev) * 10.0
        deviation = Decimal(deviation).quantize(Decimal('0.01'))
        return deviation


class TeamDetailView(DetailView):
    model = Team

    def get_context_data(self, **kwargs):
        context = super(TeamDetailView, self).get_context_data(**kwargs)

        swimmers = Swimmer.objects.filter(team__pk=context['team'].pk)
        swimmers = swimmers.order_by('grade').reverse()
        context['swimmers'] = swimmers

        return context


class TestView(TemplateView):
    template_name = 'swimrecord/test.html'

    def get_context_data(self, **kwargs):
        context = super(TestView, self).get_context_data(**kwargs)
        context['hoge'] = 'fuga'
        return context
