import snoo
import datetime
import os
import requests
import pytz

local_tz = pytz.timezone('America/New_York')

BABY_CONNECT_USERNAME = os.getenv('BABY_CONNECT_USERNAME')
BABY_CONNECT_PASSWORD = os.getenv('BABY_CONNECT_PASSWORD')

BABY_CONNECT_AUTH_URL = 'https://www.baby-connect.com/Cmd?cmd=UserAuth'
BABY_CONNECT_DATA_POST_URL = 'https://www.babyconnect.com/CmdPostW?cmd=StatusPost'

# TODO: Pull from API
BABY_CONNECT_KID_ID = 5243046970130432

SNOO_HISTORICAL_MODE = True

# TODO: Pull from API
BABY_CONNECT_CHILD_NAME = 'Samuel Isaac'

def http(request):
    main()

def convert(seconds):
    minutes = seconds / 60
    hour, min = divmod(minutes, 60)
    return "%dh%dm" % (hour, min)

def main():
    client = snoo.Client()

    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)

    sessions_list = []
    if SNOO_HISTORICAL_MODE:
        sessions = client.get_history(yesterday, today)
        for session in sessions:
            sessions_list.append(session)
    else:
        session = client.get_current_session()
        sessions_list.append(session)

    for day in sessions_list:
        for session in day.sessions:
            session = session.to_dict()
            if session['end_time']:
                try:
                    start_time = datetime.datetime.strptime(session['start_time'],
                                                            '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.timezone('UTC'))
                    end_time = datetime.datetime.strptime(session['end_time'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.timezone('UTC'))
                    current_date = datetime.datetime.strptime(session['start_time'],
                                                            '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.timezone('UTC'))
                    duration = session['duration']
                    txt_string = f'{BABY_CONNECT_CHILD_NAME} slept for {convert(duration)}'

                    end_string = datetime.datetime.strftime(end_time.astimezone(local_tz),
                                                            '%-m/%d/%Y %H:%M')

                    print(f'start time: {start_time}, end time: {end_time},\
                          current_date: {current_date}, duration:\
                          {convert(duration)}')
                except ValueError as e:
                    print('Error converting time: %s' % (e))

                with requests.Session() as s:
                    params = {'email': BABY_CONNECT_USERNAME,
                               'pass': BABY_CONNECT_PASSWORD
                             }
                    s.post(
                        BABY_CONNECT_AUTH_URL,
                        data=params,
                        headers = {'content-type': 'application/x-www-form-urlencoded'})

                    request_cookies = s.cookies
                    seacloud_cookie = request_cookies.get('seacloud1')

                    params = {'C': 500,
                              'Kid': BABY_CONNECT_KID_ID,
                              'uts': start_time.astimezone(local_tz).strftime('%H%M'),
                              'ptm': end_time.astimezone(local_tz).strftime('%H%M'),
                              'pdt': current_date.astimezone(local_tz).strftime('%y%m%d'),
                              'fmt': 'long',
                              'd': round(duration / 60),
                              'tz': -5,
                              'listKid': -1,
                              'txt': text_string,
                              'e': end_string,
                             }

                    print(params)

                    response = s.post(BABY_CONNECT_DATA_POST_URL,
                                    data=params,
                                    headers = {'content-type':
                                               'application/x-www-form-urlencoded',
                                              },
                                      cookies={'seacloud1': seacloud_cookie})

                    print(response.text)

if __name__ == "__main__":
    main()

