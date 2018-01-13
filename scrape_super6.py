import re
import datetime
import http.client
import urllib
from collections import Counter
from dateutil.parser import parse as dateparser

from bs4 import BeautifulSoup as bs
import requests

from config import keys

URL = 'https://super6.skysports.com/'


def pushover_notification(body):
    '''
    This functions sends a notification using Pushover
        Args:
            body (str) : Body of text.
    '''
    conn = http.client.HTTPSConnection("api.pushover.net")
    conn.request("POST", "/1/messages.json",
                 urllib.parse.urlencode({
                     "token": keys['token'],
                     "user": keys['user'],
                     "message": body,
                 }), {"Content-type": "application/x-www-form-urlencoded"})
    response = conn.getresponse()
    if response.status != 200:
        raise Exception('Something wrong')
    else:
        print('Sent Notification')


def get_html():
    r = requests.get(URL)
    return r.text


def parse_html(html):
    soup = bs(html, 'html.parser')
    para = soup.find('p', attrs={'class': 'deadline'})
    return para.text


def get_time(string):
    timeRegex = re.compile(r'\d{1,2}:\d{2}\w{2}')
    sear = re.search(timeRegex, string)
    return sear.group(0)


def get_date(string):
    deadline_date = string.split(',')
    deadline_date = deadline_date[1].strip('.')
    return deadline_date.lstrip()


def combine_date_str(deadtime, deaddate):
    time_date = '{} {}'.format(deadtime, deaddate)
    return time_date


def get_pundit_scores():
    pundit_url = 'https://super6.skysports.com/pundits'

    r = requests.get(pundit_url)
    soup = bs(r.text, 'html.parser')

    pundit_predictions = soup.find_all(
        'div', {'class': 'col-xs-12 matches js-match-container hidden'})

    pundits = soup.find_all(
        'div', {'class': 'col-xs-8 col-sm-9 clear-left-padding margin-top margin-bottom pundit-info'})

    pundit_names = [i.h4.text for i in pundits]
    score_dict = []

    for scores in pundit_predictions:
        predictions = scores.find_all('img')
        score_entry = scores.find_all("div", {"class": "col-xs-4 score-entry"})
        score_entry_list = [int(i.text.strip()) for i in score_entry]
        teams = [i['title'] for i in predictions]
        team_goal = list(zip(teams, score_entry_list))
        score_dict.append(dict((team, entry) for team, entry in team_goal))

    counter = Counter()
    for d in score_dict:
        counter.update(d)

    total_goals = dict(counter)
    average_goals = {}

    for k, v in total_goals.items():
        average_goals[k] = round(v / len(pundit_names))

    avg_goals_list = list(average_goals.items())

    prepare_msg = []
    for i in range(0, len(avg_goals_list), 2):
        prepare_msg.append('{} {} {} {}\n'.format(avg_goals_list[i][0], avg_goals_list[
            i][1], avg_goals_list[i + 1][0], avg_goals_list[i + 1][1]))
    return ''.join(prepare_msg)


if __name__ == '__main__':
    html = get_html()
    deadline_html = parse_html(html)
    dtime = get_time(deadline_html)
    ddate = get_date(deadline_html)
    combined_datetime = combine_date_str(dtime, ddate)
    datetime_obj = dateparser(combined_datetime)
    current_time = datetime.datetime.now()
    seconds = (datetime_obj - current_time).total_seconds()
    msg = 'Super6 deadline {}'.format(combined_datetime)
    if seconds > 0 and seconds <= 43200:
        pushover_notification('{}\n\n{}'.format(msg, get_pundit_scores()))
    else:
        print(msg)
