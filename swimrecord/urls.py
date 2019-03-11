from django.conf.urls import url
from .views import HomeView, TestView


urlpatterns = [
    url(r'^$', HomeView.as_view(), name="home"),
    url(r'test/', TestView.as_view(), name='css_test'),
]
