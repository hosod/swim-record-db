from django.core.management.base import BaseCommand
from swimrecord.management.commands.lib.Scraper import Scraper


class Command(BaseCommand):
    help = 'Scrape data from swimrecord.com and update the DataBase.'

    def add_arguments(self, parser):
        parser.add_argument('code', type=str)

    def handle(self, *args, **options):
        base_url = 'http://www.swim-record.com/swims/ViewResult/?h=V1000&code='
        scraper = Scraper('2019')

        base_url = base_url + options['code']
        scraper.set_meeting(base_url)
