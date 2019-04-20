import datetime
import urllib.parse
import sys
from urllib.request import urlopen
from bs4 import BeautifulSoup, element
from django.shortcuts import get_object_or_404
from swimrecord.models import Team, Meeting, Record, Swimmer, Event


# meeting list:試合結果一覧のページのこと
# event table:各試合の種目一覧のtableのこと

class Scraper:
    def __init__(self, hosted_year):
        self.hosted_year = hosted_year
        # 引数で受け取った年度の大会一覧のurl
        self.meeting_list_url = 'http://www.swim-record.com/taikai/%s/50.html' % hosted_year.replace('20', '')
        self.base_url = 'http://www.swim-record.com'
        self.this_year = 2018

    # meeting listのtableの１列を引数として受け取り、
    # 各試合のevent tableのurlを返す
    def __get_meeting_url_from_meeting_list(self, cells):
        a = cells[5].find('a')
        if a is None:
            return None
        else:
            link = a.get('href').split('/')
            del link[0:2]
            meeting_url = self.base_url
            for arg in link:
                meeting_url += ('/' + arg)
            return meeting_url

    # meeting listのtableの１列を引数として受け取り、試合が長水路かどうかを返す
    @staticmethod
    def __is_long(cells):
        img = cells[2].find('img')
        file_name = img.get('src').split('/')[3]
        if 'long' in file_name:
            return True
        else:
            return False

    # meeting listのtableの１列を引数として受け取り、試合の開催日を返す
    def __get_date(self, cells):
        date_str = cells[0].getText().split('〜').pop()
        date_dt = datetime.datetime.strptime((self.hosted_year + '/' + date_str), '%Y/%m/%d')
        new_year = datetime.datetime(year=int(self.hosted_year), month=4, day=1)
        if new_year > date_dt:
            date_dt = datetime.datetime(year=(int(self.hosted_year) + 1), month=date_dt.month, day=date_dt.day)
            # date_dt.year = int(self.hosted_year) + 1
        return datetime.date(date_dt.year, date_dt.month, date_dt.day)

    # 試合の名前を引数にしてDBに存在するかどうかを返す　
    @staticmethod  1    
    def __meeting_exists_in_database(meeting_name, date):
        meetings = Meeting.objects.filter(name__exact=meeting_name)
        meetings = Meeting.objects.filter(date=date)
        if meetings.count() == 0:
            return False
        else:
            meetings = meetings.filter()
            return True

    # meeting list からすでに試合結果が掲載されている試合情報をスクレイピングする
    def __scrape_meeting_list(self):
        html = urlopen(self.meeting_list_url)
        bsObj = BeautifulSoup(html, 'html.parser')
        result = bsObj.find(class_='result_main')
        table = result.find('table')
        rows = table.findAll('tr')
        del rows[0]
        meeting_list = []
        for row in rows:
            cells = row.findAll('td')
            meeting_name = cells[1].text.split(' ')[0]
            meeting_date = self.__get_date(cells)
            meeting_url = self.__get_meeting_url_from_meeting_list(cells)
            if meeting_url is None:
                continue
            else:
                meeting_is_long = Scraper.__is_long(cells)
            new_row = [meeting_name, meeting_date, meeting_is_long, meeting_url]
            meeting_list.append(new_row)
        return meeting_list

    # Meetingのテーブルにレコードを追加してTrueを返す
    # ただし、すでに存在していた場合はFalseを返して終了
    @staticmethod
    def __set_meeting(name, date, is_long, url):
        if Scraper.__meeting_exists_in_database(name, date):
            # 受け取った試合のデータがすでにDBに格納されている時
            return False
        else:
            # 受け取った試合のデータがまだDBに格納されていない時
            Meeting.objects.create(name=name, date=date, is_long=is_long, url=url)
            return True

    def set_meeting(self, meeting_url):
        html = urlopen(meeting_url)
        bsObj = BeautifulSoup(html, 'html.parser')
        header = bsObj.find(class_='headder')
        print(header)
        table = header.find('table')
        rows = table.findAll('tr')
        if '長水路' in rows[1].text:
            is_long = True
        else:
            is_long = False
        name = rows[1].text.split(':')[1]
        name = name.split('\u3000')[0]
        date_str = rows[0].text.split(' ')[0].replace('\n', '')
        date_dt = datetime.datetime.strptime(date_str, '%Y/%m/%d')
        date_dt = datetime.date(year=date_dt.year, month=date_dt.month, day=date_dt.day)

        flag = Scraper.__set_meeting(name=name, date=date_dt, is_long=is_long, url=meeting_url)

        if flag:
            # DBにレコードを挿入した時
            meeting = Meeting.objects.get(name=name)
            self.set_record(meeting)
        else:
            pass

    # 指定年度(hosted_year)の学連の試合情報をまとめてDBに挿入
    # また、挿入できたMeetingのレコードのlistを返す
    def set_meeting_list(self):
        meeting_list = self.__scrape_meeting_list()
        result = []
        for meeting in meeting_list:
            is_successful = Scraper.__set_meeting(name=meeting[0], date=meeting[1], is_long=meeting[2], url=meeting[3])
            if is_successful:
                result.append(Meeting.objects.get(name=meeting[0]))
        return result

    # this_year時点で4回生までの選手だけを追跡したい
    # 条件に合えばTrue、合わなければFalseを返す
    def filter_by_grade(self, grade):
        arg = self.this_year - int(self.hosted_year)
        if grade > (4 - arg):
            return False
        else:
            return True

    def __set_swimmer(self, name, team_name, grade):
        team = Team.objects.filter(name=team_name)
        if self.filter_by_grade(grade):
            if team.count() > 0:
                if Swimmer.objects.filter(name=name).count() > 0:
                    return Swimmer.objects.get(name=name)
                else:
                    Swimmer.objects.create(name=name, team=team.first(), grade=grade)
                    return Swimmer.objects.get(name=name)
            else:
                # 2部の大学でない
                return None
        else:
            # 選手の学年的に必要がない
            return None

    @staticmethod
    def __to_decimal(record):
        try:
            if record == '':
                return 5.0 * (10.0**3)
            else:
                time = list(map(float, record.split(':')))
                if len(record) > 5:
                    second = time[1]
                    minute = time[0]
                    return second + (minute * 60.0)
                else:
                    return time[0]
        except ValueError:
            return 5.0 * (10.0**3)

    @staticmethod
    def __set_record(swimmer, meeting, event, record):
        Record.objects.create(swimmer=swimmer, meeting=meeting, event=event, record=record)

    # result_meeting: [Swimmer.name, Team.name, Event.name, record, grade]のlist
    def set_record(self, meeting):
        result_meeting = self.__scrape_result_of_meeting(meeting)
        counter = 0
        for row in result_meeting:
            swimmer = self.__set_swimmer(name=row[0], team_name=row[1], grade=row[4])
            if swimmer is not None:
                event = Event.objects.get(name=row[2])
                Scraper.__set_record(swimmer, meeting, event, record=row[3])
                counter += 1
            else:
                # swimmerが2部の大学の選手でない、
                # またはデータが必要のない学年で、__set_swimmerがNoneを返した時
                continue
        print(counter)

    # target_argのなかにTeamの要素があるかどうかを判定
    @staticmethod
    def __contains_team(target_arg):
        teams = Team.objects.all()
        for team in teams:
            if team.name in target_arg:
                return True
            else:
                continue
        return False

    # event_table のurlを受け取り、各種目の試合結果のurlのlistを返す
    def __get_urls_from_event_table(self, event_table_url):
        html = urlopen(event_table_url)
        bsObj = BeautifulSoup(html, 'html.parser')
        table = bsObj.findAll('table')[2]
        rows = table.findAll('a')
        urls = []
        for row in rows:
            new_url = self.base_url + row.get('href')
            urls.append(new_url)
        return urls

    # urlの種目の試合結果についてスクレイピングする
    @staticmethod
    def __scrape_result_of_event(url):
        html = urlopen(url)
        bsObj = BeautifulSoup(html, 'html.parser')
        tables = bsObj.findAll('table')
        tables = [s for s in tables if Scraper.__contains_team(str(s))]
        rows = element.ResultSet([])
        for table in tables:
            rows.extend(table.findAll('tr', {'align': 'center'}))
        event_data = []
        for row in rows:
            new_row = []
            for cell in row.findAll(['td', 'th']):
                text = cell.get_text().replace('\n', '').replace(' ', '')
                text = text.replace('\xa0', '').replace('\u3000', '').replace('\r', '')
                new_row.append(text)
            if new_row[6].isdecimal():
                event_data.append(new_row)
            else:
                continue

        return event_data

    # 種目urlから種目の判定
    @staticmethod
    def __classify_event(url):
        params = urllib.parse.parse_qs(url)
        event = params['event']
        distance = params['distance']

        if int(event[0]) == 1:
            target_event = 'Fr'
        elif int(event[0]) == 2:
            target_event = 'Ba'
        elif int(event[0]) == 3:
            target_event = 'Br'
        elif int(event[0]) == 4:
            target_event = 'Fly'
        elif int(event[0]) == 5:
            target_event = 'IM'
        elif int(event[0]) == 6:
            target_event = 'FR'
        elif int(event[0]) == 7:
            target_event = 'MR'
        else:
            print('Error_event.')
            sys.exit()

        if int(distance[0]) == 2:
            target_dist = '50'
        elif int(distance[0]) == 3:
            target_dist = '100'
        elif int(distance[0]) == 4:
            target_dist = '200'
        elif int(distance[0]) == 5:
            target_dist = '400'
        elif int(distance[0]) == 6:
            target_dist = '800'
        elif int(distance[0]) == 7:
            target_dist = '1500'
        else:
            print('Error_distance')
            sys.exit()
        return target_dist + target_event

    # 引数に与えられたMeetingについて試合結果の
    # [Swimmer.name, Team.name, Event.name, record, grade]のlistを返す
    def __scrape_result_of_meeting(self, meeting):
        meeting_result = []
        # 各種目のurl
        event_urls = self.__get_urls_from_event_table(meeting.url)
        for url in event_urls:
            event_result = Scraper.__scrape_result_of_event(url)
            event_name = Scraper.__classify_event(url)
            for row in event_result:
                row[3] = row[3].replace('大学', '')
                # 学年が存在しているかどうか判定
                if row[3].isdecimal():
                    new_row = [row[1], row[2], event_name, Scraper.__to_decimal(row[4]), int(row[3])]
                    meeting_result.append(new_row)
                else:
                    continue

        return meeting_result
