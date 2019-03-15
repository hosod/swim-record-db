from django.db import models
from django.utils import timezone


# Create your models here.
class Meeting(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    is_long = models.BooleanField(default=False)
    url = models.URLField('http://www.swim-record.com/')

    # def set_date(self, data):
    #     self.date = timezone(data)
    #     self.save()

    def __str__(self):
        return self.name + '(' + str(self.date) + ')'


class Team(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Swimmer(models.Model):
    name = models.CharField(max_length=100)
    team = models.ForeignKey('swimrecord.Team', on_delete=models.CASCADE, related_name='swimmers')
    grade = models.SmallIntegerField()

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Record(models.Model):
    swimmer = models.ForeignKey('swimrecord.Swimmer', on_delete=models.CASCADE, related_name='records')
    meeting = models.ForeignKey('swimrecord.Meeting', on_delete=models.CASCADE, related_name='records')
    event = models.ForeignKey('swimrecord.Event', on_delete=models.CASCADE, related_name='records')
    record = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return  str(self.swimmer) + str(self.event.name) + str(self.record)
