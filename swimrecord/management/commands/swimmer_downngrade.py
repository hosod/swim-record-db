from django.core.management.base import BaseCommand
from swimrecord.models import Swimmer


class Command(BaseCommand):
    help = '間違えたときに全選手の学年を一つ下げる'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        swimmers = Swimmer.objects.all()
        for swimmer in swimmers:
            swimmer.grade += -1
            swimmer.save()
