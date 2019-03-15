from django.conf.urls import url
from .views import RecordListView, SwimmerDetailView, TeamDetailView, TestView
from .views import EventDetailView, MeetingDetailView, MeetingEventView
from .views import MeetingListView, TeamListView, EventListView


urlpatterns = [
    url(r'^$', RecordListView.as_view(), name="record_list"),
    url(r'^swimmer/(?P<pk>[0-9]+)/$', SwimmerDetailView.as_view(), name='swimmer_detail'),
    url(r'^team/(?P<pk>[0-9]+)/$', TeamDetailView.as_view(), name='team_detail'),
    url(r'^event/(?P<pk>[0-9]+)/$', EventDetailView.as_view(), name='event_detail'),
    url(r'^meeting/(?P<pk>[0-9]+)/$', MeetingDetailView.as_view(), name='meeting_detail'),
    url(r'^meeting/event/(?P<pk>[0-9]+)/(?P<event_pk>[0-9]+)/$', MeetingEventView.as_view(), name='meeting_event'),
    url(r'^meeting-list/$', MeetingListView.as_view(), name='meeting_list'),
    url(r'^team-list/$', TeamListView.as_view(), name='team_list'),
    url(r'^event-list/$', EventListView.as_view(), name='event_list'),
    url(r'test/', TestView.as_view(), name='css_test'),
]
