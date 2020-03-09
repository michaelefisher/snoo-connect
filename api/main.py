import snoo
import datetime
import os
import requests
import pytz
import hashlib
import logging

logger = logging.Logger('Main', 1)

logger.setLevel(logging.INFO)

local_tz = pytz.timezone('America/New_York')

BABY_CONNECT_USERNAME = os.getenv('BABY_CONNECT_USERNAME')
BABY_CONNECT_PASSWORD = os.getenv('BABY_CONNECT_PASSWORD')

BABY_CONNECT_AUTH_URL = 'https://www.baby-connect.com/Cmd?cmd=UserAuth'
BABY_CONNECT_DATA_POST_URL = 'https://www.babyconnect.com/CmdPostW?cmd=StatusPost'
BABY_CONNECT_DATA_LIST_URL = 'https://www.babyconnect.com/CmdPostW?cmd=StatusList'

BABY_CONNECT_KID_ID = os.getenv('BABY_CONNECT_KID_ID')

SNOO_HISTORICAL_MODE = os.getenv('SNOO_HISTORICAL_MODE')

BABY_CONNECT_CHILD_NAME = os.getenv('BABY_CONNECT_CHILD_NAME')

BABY_CONNECT_DAY_LIMIT = os.getenv('BABY_CONNECT_DAY_LIMIT')

def pubSub(event):
    main()

def convert(seconds):
    minutes = seconds / 60
    hour, min = divmod(minutes, 60)
    return "%dh%dm" % (hour, min)

def is_sleeping(session_dict):
    now = datetime.datetime.now()
    if session_dict['end_time'] > now.strftime('%Y-%m-%dT%H:%M:%S'):
        print('We\'re still sleeping.')

def send_data(session_params):
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
                  'uts': session_params['start_time'].astimezone(local_tz).strftime('%H%M'),
                  'ptm': session_params['end_time'].astimezone(local_tz).strftime('%H%M'),
                  'pdt': session_params['current_date'].astimezone(local_tz).strftime('%y%m%d'),
                  'fmt': 'long',
                  'd': round(session_params['duration'] / 60),
                  'tz': -4,
                  'listKid': -1,
                  'txt': session_params['text_string'],
                  'e': session_params['end_string'],
                 }

        response = s.post(BABY_CONNECT_DATA_POST_URL,
                        data=params,
                        headers = {'content-type':
                                   'application/x-www-form-urlencoded',
                                  },
                          cookies={'seacloud1': seacloud_cookie})

        logger.info(response)

def main():
    client = snoo.Client()

    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)

    sessions_list = []
    if SNOO_HISTORICAL_MODE:
        # Get sessions from the past 24 hours
        sessions = client.get_history(yesterday, today)
        for session in sessions:
            sessions_list.append(session)
    else:
        session = client.get_current_session()
        sessions_list.append(session)
    for day in sessions_list:
        for session in day.sessions:
            print(day.sessions)
            session = session.to_dict()
            is_sleeping(session)
            if session['start_time']:
                try:
                    start_time = datetime.datetime.strptime(session['start_time'],
                                                            '%Y-%m-%dT%H:%M:%S').replace(tzinfo=local_tz)
                    end_time = datetime.datetime.strptime(session['end_time'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=local_tz)

                    current_date = datetime.datetime.strptime(session['start_time'],
                                                            '%Y-%m-%dT%H:%M:%S').replace(tzinfo=local_tz)
                    duration = session['duration']
                    text_string = f'{BABY_CONNECT_CHILD_NAME} slept for {convert(duration)}'

                    end_string = datetime.datetime.strftime(end_time.astimezone(local_tz),
                                                            '%-m/%d/%Y %H:%M')

                    logger.info(f'start time: {start_time}, end time: {end_time}')
                    logger.info(f'current_date: {current_date}, duration: {convert(duration)}')
                except ValueError as e:
                    logger.info('Error converting time: %s' % (e))

                session_params = {}
                session_params['start_time'] = start_time
                session_params['end_time'] = end_time
                session_params['duration'] = duration
                session_params['current_date'] = current_date
                session_params['text_string'] = text_string
                session_params['end_string'] = end_string

                send_data(session_params)

if __name__ == "__main__":
    main()


