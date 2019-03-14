from django.conf.urls import url
from .views import RecordListView, TestView


urlpatterns = [
    url(r'^$', RecordListView.as_view(), name="record_list"),

    url(r'test/', TestView.as_view(), name='css_test'),
]
