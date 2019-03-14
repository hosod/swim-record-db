from django.conf.urls import url
from .views import RecordListView, SwimmerDetailView, TeamDetailView, TestView


urlpatterns = [
    url(r'^$', RecordListView.as_view(), name="record_list"),
    url(r'^swimmer/(?P<pk>[0-9]+)/$', SwimmerDetailView.as_view(), name='swimmer_detail'),
    url(r'^team/(?P<pk>[0-9]+)/$', TeamDetailView.as_view(), name='team_detail'),
    url(r'test/', TestView.as_view(), name='css_test'),
]
