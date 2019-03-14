from django.conf.urls import url
from .views import RecordListView, SwimmerDetailView, TestView


urlpatterns = [
    url(r'^$', RecordListView.as_view(), name="record_list"),
    url(r'^swimmer/(?P<pk>[0-9]+)/$', SwimmerDetailView.as_view(), name='swimmer_detail'),
    url(r'test/', TestView.as_view(), name='css_test'),
]
