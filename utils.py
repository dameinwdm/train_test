# -*- coding: utf-8 -*-

"""
iquery.utils
~~~~~~~~~~~~~

A simple args parser and a color wrapper.
"""

import sys
import random
import requests
import datetime

from requests.exceptions import ConnectionError, Timeout


__all__ = ['args', 'colored', 'requests_get', 'exit_after_echo']

def requests_get(url, **kwargs):
    requests.packages.urllib3.disable_warnings()
    today = datetime.date.today()
    from_station = kwargs['params'].get('leftTicketDTO.from_station')
    to_station = kwargs['params'].get('leftTicketDTO.to_station')
    from_station_name = kwargs['params'].get('leftTicketDTO.from_station_name')
    to_station_name = kwargs['params'].get('leftTicketDTO.to_station_name')
    purpose_code =  kwargs['params'].get('purpose_codes')
    train_date = kwargs['params'].get('leftTicketDTO.train_date')
    USER_AGENTS = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100 101 Firefox/22.0',
        'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
        ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_4) AppleWebKit/536.5 (KHTML, like Gecko) '
         'Chrome/19.0.1084.46 Safari/536.5'),
        ('Mozilla/5.0 (Windows; Windows NT 6.1) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.46'
         'Safari/536.5')
    )
    post_data = {'back_train_date': today.strftime("%Y-%m-%d"),
                 '_json_att': "", 'flag': 'dc',
                 'leftTicketDTO.from_station': from_station,
                 'leftTicketDTO.to_station':to_station,
                 'leftTicketDTO.from_station_name': from_station_name,
                 'leftTicketDTO.to_station_name': to_station_name,
                 'leftTicketDTO.train_date': train_date,
                 'pre_step_flag': 'index',
                 'purpose_code': purpose_code }
    init_resp = requests.post('https://kyfw.12306.cn/otn/leftTicket/init', data=post_data,
                              headers={'User-Agent': random.choice(USER_AGENTS)}, allow_redirects=True, verify=False)
    cookies = init_resp.cookies
    cookies.set('_jc_save_fromStation',from_station_name + ',' + from_station, domain='kyfw.12306.cn', path='/')
    cookies.set('_jc_save_toStation',to_station_name + ',' + to_station, domain='kyfw.12306.cn', path='/')
    cookies.set('_jc_save_fromDate',train_date, domain='kyfw.12306.cn', path='/')
    cookies.set('_jc_save_toDate', today.strftime("%Y-%m-%d"), domain='kyfw.12306.cn', path='/')
    cookies.set('_jc_save_wfdc_flag', 'dc', domain='kyfw.12306.cn', path='/')
    po_url = url + "leftTicketDTO.train_date=" + train_date + "&leftTicketDTO.from_station=" + from_station + "&leftTicketDTO.to_station=" + to_station + "&purpose_codes=ADULT"

    try:
        r = requests.get(
            po_url,
            headers={'User-Agent': random.choice(USER_AGENTS)} ,timeout=12,cookies=cookies
        )
    except ConnectionError:
        pass
    except Timeout:
       pass
    return r
