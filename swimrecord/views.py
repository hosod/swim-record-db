from django.views.generic import TemplateView, ListView, DetailView
from pure_pagination import PaginationMixin
from django.db import models
from django.http import request
from .models import Record, Meeting, Team, Event, Swimmer
from .forms import SearchForm
from statistics import mean, stdev
from decimal import Decimal


# Create your views here.
class HomeView(ListView):
    template_name = 'swimrecord/home.html'
    model = Swimmer

    teams = Team.objects.all()

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['teams'] = self.teams

        point_swimmer = self.cal_swimmer_points()
        rank_swimmer = self.rank(point_swimmer[0:20])
        data_swimmer = list()
        # 得点表示は上位20人まで
        for index in range(20):
            name = point_swimmer[index][0]
            swimmer = Swimmer.objects.get(name=name)
            data_swimmer.append((swimmer, point_swimmer[index][1], rank_swimmer[index]))
        context['data_swimmer'] = data_swimmer

        point_univ = self.cal_univ_points(point_swimmer)
        rank_univ = self.rank(point_univ)
        data_univ = list()
        for index in range(8):
            univ = point_univ[index]
            data_univ.append((univ[0], univ[1], rank_univ[index]))
        context['data_univ'] = data_univ

        return context

    # return list[tuple{name(swimmer), points}].sorted
    @staticmethod
    def cal_swimmer_points():
        exceptions = Event.objects.filter(name__startswith='50')[1:4]
        events = set(Event.objects.all()).difference(exceptions)

        points_dic = dict()
        for event in events:
            records = event.records.filter(meeting__is_long=True)
            ranking = records.values('swimmer__name').annotate(models.Min('record')).order_by('record__min')
            ranking = ranking[0:8]
            for index in range(ranking.count()):
                name = ranking[index]['swimmer__name']
                if name in points_dic.keys():
                    points_dic[name] += (8 - index)
                else:
                    points_dic[name] = (8 - index)
        return sorted(points_dic.items(), key=lambda x: -x[1])

    # return list[tuple(team, points)]
    def cal_univ_points(self, point_tps):
        # point_tps: list[tuple{name(swimmer or team), points}]
        point_univ = dict()
        for team in self.teams:
            point_univ[team] = 0

        for index in range(len(point_tps)):
            name = point_tps[index][0]
            swimmer = Swimmer.objects.get(name=name)
            team = swimmer.team
            point_univ[team] += point_tps[index][1]

        return sorted(point_univ.items(), key=lambda x: -x[1])

    # return list[rank(int)]
    @staticmethod
    def rank(points_tps):
        # point_tps: list[tuple{name(swimmer or team), points}]
        points = points_tps[0][1]
        current_rank = 1
        same = 1
        pre_pt = points
        result = [current_rank]

        for index in range(1, len(points_tps)):
            points = points_tps[index][1]
            if points < pre_pt:
                # 同率じゃないとき
                current_rank += same
                same = 1
                pre_pt = points
            else:
                # 同率のとき
                same += 1
            result.append(current_rank)
        return result

    def get_queryset(self):
        # デフォルトでは0件
        results = self.model.objects.all()

        q_name = self.request.GET.get('name')
        print(q_name)
        if q_name is None:
            # 検索結果なしにしたい
            # 他にいい書き方があったら書き換える！！
            results = results.filter(name='hoge')
        else:
            results = results.filter(name__contains=q_name)
        return results


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

        history = self.records.filter(swimmer__pk=context['swimmer'].pk).order_by('meeting__date').reverse()

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


class EventDetailView(DetailView):
    model = Event

    def get_context_data(self, **kwargs):
        context = super(EventDetailView, self).get_context_data(**kwargs)
        data = dict()
        data['long'] = self.__get_data(is_long=True)
        data['short'] = self.__get_data(is_long=False)
        context['data'] = data

        return context

    def __get_data(self, is_long):
        ranking = Record.objects.filter(event__pk=self.kwargs['pk']).filter(record__lt=5000)
        ranking = ranking.filter(meeting__is_long=is_long)
        ranking = ranking.values('swimmer__name').annotate(models.Min('record')).order_by('record__min')

        data = []
        for record in ranking:
            deviation = self.__get_deviation(ranking, record['record__min'])
            swimmer = Swimmer.objects.get(name=record['swimmer__name'])
            data.append({'swimmer_name': record['swimmer__name'],
                         'swimmer_pk': swimmer.pk,
                         'swimmer_grade': swimmer.grade,
                         'team': swimmer.team,
                         'record': record['record__min'],
                         'deviation': deviation
                         })
        return data

    @staticmethod
    def __get_deviation(ranking, record):
        ranking = ranking.values_list('record__min')
        ranking = list(map((lambda x: float(x[0])), ranking))
        avg = mean(ranking)
        std_ev = stdev(ranking)

        deviation = 50.0 - ((float(record) - avg) / std_ev) * 10.0
        deviation = Decimal(deviation).quantize(Decimal('0.01'))
        return deviation


class MeetingDetailView(PaginationMixin, DetailView):
    model = Meeting

    def get_context_data(self, **kwargs):
        context = super(MeetingDetailView, self).get_context_data(**kwargs)
        meeting_events = context['meeting'].records.values('event__name').distinct()
        meeting_events = Event.objects.filter(name__in=meeting_events)
        context['events'] = meeting_events
        return context


class MeetingEventView(DetailView):
    model = Meeting
    template_name = 'swimrecord/meeting_event.html'

    def get_context_data(self, **kwargs):
        context = super(MeetingEventView, self).get_context_data(**kwargs)

        event = Event.objects.get(pk=self.kwargs['event_pk'])

        records = Record.objects.filter(event__pk=self.kwargs['event_pk'])
        records = records.filter(meeting__pk=self.kwargs['pk'])
        records = records.order_by('record')

        context['records'] = records
        context['event'] = event
        return context


class MeetingListView(ListView):
    queryset = Meeting.objects.all().order_by('date').reverse()

    def get_context_data(self, **kwargs):
        context = super(MeetingListView, self).get_context_data(**kwargs)

        data = {}
        data['long'] = self.queryset.filter(is_long=True)
        data['short'] = self.queryset.filter(is_long=False)

        context['data'] = data

        return context


class TeamListView(ListView):
    model = Team

    def get_context_data(self, **kwargs):
        context = super(TeamListView, self).get_context_data(**kwargs)
        return context


class EventListView(ListView):
    model = Event

    def get_context_data(self, **kwargs):
        context = super(EventListView, self).get_context_data(**kwargs)
        return context


class TestView(TemplateView):
    template_name = 'swimrecord/test.html'

    def get_context_data(self, **kwargs):
        context = super(TestView, self).get_context_data(**kwargs)

        short = Event.objects.filter(name__startswith='50')[1:4]
        events = set(Event.objects.all()).difference(short)

        point_dc = {}
        for event in events:
            records = event.records.filter(meeting__is_long=True)
            ranking = records.values('swimmer__name').annotate(models.Min('record')).order_by('record__min')
            ranking = ranking[0:8]
            for rank in range(ranking.count()):
                name = ranking[rank]['swimmer__name']
                if name in point_dc.keys():
                    point_dc[name] += (8 - rank)
                else:
                    point_dc[name] = (8 - rank)
        point_dc = sorted(point_dc.items(), key=lambda x: -x[1])
        point_sw = []
        point_univ = {}

        for team in Team.objects.all():
            point_univ[team] = 0

        for index in range(len(point_dc)):
            name = point_dc[index][0]
            swimmer = Swimmer.objects.get(name=name)
            team = swimmer.team
            point_univ[team] += point_dc[index][1]
            point_sw.append((swimmer, point_dc[index][1]))

        point_univ = sorted(point_univ.items(), key=lambda x: -x[1])

        data = list()
        rank_univ = self.rank(point_univ)
        for i in range(8):
            univ = point_univ[i]
            data.append((univ[0], univ[1], rank_univ[i]))
        context['data_univ'] = data
        data = list()
        rank_swimmer = self.rank(point_sw)
        for i in range(20):
            swimmer = point_sw[i]
            data.append((swimmer[0], swimmer[1], rank_swimmer[i]))
        context['data_swimmer'] = data

        context['teams'] = Team.objects.all()
        context['events'] = Event.objects.all()
        context['meetings'] = Meeting.objects.all().order_by('date')[0:15]
        return context

    @staticmethod
    def rank(point_sw):
        name, point = point_sw[0]
        current = 1
        same = 1
        pre_pt = point
        result = list()
        result.append(current)

        for index in range(1, len(point_sw)):
            name, point = point_sw[index]
            if point < pre_pt:
                current = current + same
                same = 1
                pre_pt = point
            else:
                same += 1
            result.append(current)

        return result

