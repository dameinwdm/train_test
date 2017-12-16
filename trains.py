# -*- coding: utf-8 -*-

"""
iquery.trains
~~~~~~~~~~~~~~

Train tickets query and display. The datas come
from:
    www.12306.cn
"""

import os
import re
import tempfile
try:
    import cPickle as pickle
except ImportError:
    import pickle
from datetime import datetime
from collections import OrderedDict
from utils import  requests_get
import json
import sys
defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)


__all__ = ['query','trains',"train_post"]

QUERY_URL = 'https://kyfw.12306.cn/otn/leftTicket/query?'
# ERR
FROM_STATION_NOT_FOUND = 'From station not found.'
TO_STATION_NOT_FOUND = 'To station not found.'
INVALID_DATE = 'Invalid query date.'
TRAIN_NOT_FOUND = 'No result.'
NO_RESPONSE = 'Sorry, server is not responding.'

class TrainsCollection(object):

    """A set of raw datas from a query."""



    def __init__(self, rows, opts):
        self._rows = rows['data']['result']
        self.map = rows['data']['map']
        self._opts = opts
        self.opencar_str = "预订"
        self.stopcar_str = "列车停运"
    def __repr__(self):
        return '<TrainsCollection size={}>'.format(len(self))

    def __len__(self):
        return len(self._rows)

    def _get_duration(self, row):
        duration = row.get('lishi').replace(':', '小时') + '分钟'
        # take 0 hour , only show minites
        if duration.startswith('00'):
            return duration[4:]
        # take <10 hours, show 1 bit
        if duration.startswith('0'):
            return duration[1:]
        return duration
    @property
    def trains(self):
        train={}
        code = TrainTicketsQuery(None,None,None,None)
        d = code.stations
        new_dict = {v: k for k, v in d.items()}
        for times in range(len(self._rows)):
            line = self._rows[times]
            start = line.find(self.opencar_str)
            opencar_line = line[start:-1]
            new_line = opencar_line.split('|')
            if len(new_line) > 2:
                for i in range(len(new_line) - 1):
                    if len(new_line[i]) > 30:
                        del new_line[i]
                train['train_no'] = new_line[2]
                train['from_train'] = new_dict.get(new_line[3])
                train['to_train'] = new_dict.get(new_line[4])
                train['from_time'] = new_line[7]
                train['to_time'] = new_line[8]
                train['times'] = new_line[9]
                train['zero'] = new_line[30]
                train['one'] =new_line[29]
                train['two']=new_line[28]
                train['highsolf'] =new_line[19]
                train['solf']=new_line[21]
                train['hardsolf']=new_line[26]
                train['none']=new_line[24]
                train['hardsit']=new_line[27]
                yield train,new_line
class TrainTicketsQuery(object):

    """Docstring for TrainTicketsCollection. """

    def __init__(self, from_station, to_station, date, opts=None):
        self.from_station = from_station
        self.to_station = to_station
        self.date = date
        self.opts = opts


    def __repr__(self):
        return 'TrainTicketsQuery from={} to={} date={}'.format(
            self._from_station, self._to_station, self._date
        )

    @property
    def stations(self):
        filename = 'iquery.stations.cache'
        _cache_file = os.environ.get(
            'IQUERY_STATIONS_CACHE',
            os.path.join(tempfile.gettempdir(), filename)
        )

        if os.path.exists(_cache_file):
            try:
                with open(_cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass

        filepath = os.path.join(
            os.path.dirname(__file__),
            'datas', 'stations.dat'
        )
        d = {}
        with open(filepath, 'r') as f:
            for line in f.readlines():
                name, telecode = line.split()
                d.setdefault(name, telecode)

        with open(_cache_file, 'wb') as f:
            pickle.dump(d, f)
        return d

    @property
    def _from_station_telecode(self):
        code = self.stations.get(self.from_station)
        if not code:
            pass
        return code

    @property
    def _from_station_name_telecode(self):
        return self.from_station

    @property
    def _to_station_telecode(self):
        code = self.stations.get(self.to_station)
        if not code:
            pass
        return code

    @property

    def _to_station_name_telecode(self):
        return self.to_station
    @property
    def _valid_date(self):
        """Check and return a valid query date."""
        date = self._parse_date(self.date)

        if not date:
            pass

        try:
            date = datetime.strptime(date, '%Y%m%d')
        except ValueError:
            pass

        # A valid query date should within 50 days.
        offset = date - datetime.today()
        if offset.days not in range(-1, 50):
            pass

        return datetime.strftime(date, '%Y-%m-%d')

    @staticmethod
    def _parse_date(date):
        """Parse from the user input `date`.

        e.g. current year 2016:
           input 6-26, 626, ... return 2016626
           input 2016-6-26, 2016/6/26, ... retrun 2016626

        This fn wouldn't check the date, it only gather the number as a string.
        """
        result = ''.join(re.findall('\d', date))
        l = len(result)

        # User only input month and day, eg 6-1, 6.26, 0626...
        if l in (2, 3, 4):
            year = str(datetime.today().year)
            return year + result

        # User input full format date, eg 201661, 2016-6-26, 20160626...
        if l in (6, 7, 8):
            return result

        return

    def _build_params(self):
        """Have no idea why wrong params order can't get data.
        So, use `OrderedDict` here.
        """
        d = OrderedDict()
        d['purpose_codes'] = 'ADULT'
        d['leftTicketDTO.train_date'] = self._valid_date
        d['leftTicketDTO.from_station'] = self._from_station_telecode
        d['leftTicketDTO.to_station'] = self._to_station_telecode
        d['leftTicketDTO.from_station_name'] = self._from_station_name_telecode
        d['leftTicketDTO.to_station_name'] = self._to_station_name_telecode
        return d

    def query(self):

        params = self._build_params()
        r = requests_get(QUERY_URL, params=params, verify=False)

        try:
            rows = r.json()
        except KeyError:
            rows = []
        except TypeError:
            pass

        return TrainsCollection(rows, self.opts)


def query(params):
    """`params` is a list, contains `from`, `to`, `date`."""
    return TrainTicketsQuery(*params).query()

def train_post(FTT):
    trains_name = []
    trains_from =[]
    trains_to =[]
    trains_from_time=[]
    trains_to_time =[]
    trains_times =[]
    trains_zreo =[]
    trains_one =[]
    trains_two=[]
    trains_highsoft =[]
    trains_solf=[]
    trains_hardsolf =[]
    trains_none=[]
    trains_hardsit=[]
    d = query(FTT)
    for train, new_line in d.trains:
        trains_name.append(train.get("train_no"))
        trains_from.append(train.get("from_train"))
        trains_to.append(train.get("to_train"))
        trains_from_time.append(train.get("from_time"))
        trains_to_time.append(train.get("to_time"))
        trains_times.append(train.get("times"))
        trains_zreo.append(train.get("zero"))
        trains_one.append(train.get("one"))
        trains_two.append(train.get("two"))
        trains_highsoft.append(train.get("highsolf"))
        trains_solf.append(train.get("solf"))
        trains_hardsolf.append(train.get("hardsolf"))
        trains_none.append(train.get("none"))
        trains_hardsit.append(train.get("hardsit"))


    return trains_name,trains_from,trains_to,trains_from_time,trains_to_time,trains_times,trains_zreo,trains_one,trains_two,trains_highsoft,trains_solf,trains_hardsolf,trains_hardsit,trains_none