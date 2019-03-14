from django.core.management.base import BaseCommand
from swimrecord.management.commands.lib.Scraper import Scraper
from swimrecord.models import Meeting, Event, Record, Team


class Command(BaseCommand):
    # python manager.py help scrape_dataで表示されるhelpメッセージ
    help = 'Scrape data from swimrecord.com and update the DataBase.'

    def add_arguments(self, parser):
        parser.add_argument('hosted_year', type=str)

    def handle(self, *args, **options):
        scraper = Scraper(options['hosted_year'])
        meetings = scraper.set_meeting_list()
        print(len(meetings))
        for meeting in meetings:
            print(meeting)
            scraper.set_record(meeting)
            print(meeting.name)
