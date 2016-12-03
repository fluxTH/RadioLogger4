import exceptions
from sqlalchemy.engine.base import Engine

import requests
from requests.exceptions import (
    ConnectionError,
    Timeout
)
import socket
from yahooproxy import YahooProxy, YahooProxyException

import time

yp = YahooProxy()

class Station(object):

    _name = None
    _slug = None

    _endpoint = None
    _postPayload = None
    _dataFormat = 'json'

    _engine = None

    _log = None
    _dblog = None

    _proxy = True

    _queueInterval = 60
    _queueRanLast = None
    _queueOverride = None

    def __init__(self, engine, log, dblog):
        self.init_object()
        self.check_object()
        self.init_db(engine)
        self.init_logger(log, dblog)
        self._('Station Logger Initialized! (using proxy: {proxy})'.format(proxy=('YES' if self._proxy else 'NO')))

    def check_object(self):
        if self._endpoint is None:
            raise exceptions.NotImplementedException('This station does not have an endpoint!')

    def init_db(self, engine):
        if engine.__class__ is not Engine:
            raise exceptions.DBException('Database engine is not avaliable!')

        self._engine = engine

    def init_logger(self, log, dblog):
        self._log = log
        self._dblog = dblog

    def init_object(self):
        if self._name is None:
            self._name = self.__class__.__name__

        if self._slug is None:
            self._slug = self.__class__.__name__.lower()

    def set_interval(self, interval=60):
        self._queueInterval = interval

    def _(self, s, data=None, p='Debug', console=True, save=True):
        if save:
            self._dblog(self._slug, s, data=data, priority=p)

        if console:
            color = ''
            if p == 'Warning':
                color = 'warn'
            elif p == 'Error':
                color = 'err'

            self._log(self._slug, s, c=color)

    def run(self):
        """
        Gets called in a main Loop

        @returns Bool: called
        """
        #self._('ran last={}'.format(self._queueRanLast),save=False)

        if self._queueRanLast is None:
            self._queueRanLast = 0
            return self.execute()

        else:
            if self._queueOverride is None:
                # Regular interval calculation
                if time.time() > (self._queueRanLast + self._queueInterval):
                    return self.execute()
            else:
                # Calculate interval using overriden seconds
                if time.time() > (self._queueRanLast + self._queueOverride):
                    self._queueOverride = None
                    return self.execute()

            return False

    def execute(self):
        try:
            data = self.fetch()
        except YahooProxyException as e:
            self._('Proxy error! Trying again in 45 seconds', p='Error', data={'details': str(e)})
            self._queueOverride = 45
            return False
        except Timeout as e:
            self._('Request timed out! trying again in 60 seconds', p='Error', data={'details': str(e)})
            self._queueOverride = 60
            return False
        except ConnectionError as e:
            self._('Connection error! trying again in 30 seconds', p='Error', data={'details': str(e)})
            self._queueOverride = 30
            return False
        except socket.timeout as e:
            self._('Socket timed out! trying again in 60 seconds', p='Error', data={'details': str(e)})
            self._queueOverride = 60
            return False
        finally:
            self._queueRanLast = time.time()

        if data is False:
            return False

        parsed = self.parseData(data)
        print(parsed)

        # process and save data
        self.process_data(parsed)

        self._queueRanLast = time.time()

    def process_data(self, parsed):
        """
        {
            id: int
            type: str<SONG, LINK, SPOT, DEFAULT_METADATA>
            title: str
            artist: str
            extra_data: Dict
        }
        """
        pass

    def fetch(self):
        # TODO: Make disabling proxy possible
        self._('Getting metadata...', save=False)

        if self._postPayload is not None:
            # do a post request
            ###
            pass
        else:
            # do a get request
            if self._dataFormat.lower() == 'json':
                return yp.get_json(self._endpoint)
            elif self._dataFormat.lower() == 'html':
                return yp.get_html(self._endpoint)
            elif self._dataFormat.lower() == 'xml':
                return yp.get_xml(self._endpoint)
            else:
                raise exceptions.NotSupportedException("Not supported format '{}'!".format(self._dataFormat))

    def parseData(self, data):
        """
        Abstract Method:
        Parses data that is fetched from endpoint

        @param data<Str>: fetched data
        @returns Dict: parsed data
        """
        raise exceptions.NotImplementedException('This station cannot parse data!')

class Cool93(Station):
    _name = 'Cool 93'
    _slug = 'Cool93'

    # _endpoint = 'http://www.coolism.net/mobile-xml/fahrenheit/rcs/BILLBOARD.ASC'
    _endpoint = 'http://www.coolism.net/mobile-xml/fahrenheit/nowplaying.php'
    _dataFormat = 'xml'

    def __init__(self, *args, **kwargs):
        super(Cool93, self).__init__(*args, **kwargs)

    def parseData(self, data):
        title = data['data']['song'].strip()
        artist = data['data']['artist'].strip()

        if (title == 'COOLfahrenheit 93') and (artist == 'LIVE Online'):
            return {
                'type': 'DEFAULT_METADATA',
            }
        else:
            return {
                'type': 'SONG',
                'title': title,
                'artist': artist,
            }

class Greenwave1065(Station):
    _name = 'Greenwave 106.5'
    _slug = 'Greenwave'

    _endpoint = 'http://api.greenwave.fm/nowplaying'
    _dataFormat = 'json'

    def __init__(self, *args, **kwargs):
        super(Greenwave1065, self).__init__(*args, **kwargs)

    def parseData(self, data):
        return {
            'id': data['now']['id'],
            'type': 'SONG' if data['now']['id'] != 0 else 'DEFAULT_METADATA',
            'title': data['now']['title'],
            'artist': data['now']['artist'],
        }

class EDS885(Station):
    _name = '88.5 EDS'
    _slug = 'EDS'

    _endpoint = 'http://www.everydaystation.com/billboard'
    _dataFormat = 'xml'

    def __init__(self, *args, **kwargs):
        super(EDS885, self).__init__(*args, **kwargs)

    def parseData(self, data):
        #print(data)
        eventType = data['CueList']['Event'][0]['eventType']
        artists = ''

        meta = {
            'type': eventType.upper(),
            'title': data['CueList']['Event'][0][eventType.title()]['title'],
            'artist': artists,
            'extra_data': {
                'sequencer_mode': data['CueList']['sequencerMode'],
                'segue': data['CueList']['Event'][0]['segue'],
                'edit_code': data['CueList']['Event'][0]['editCode'],
                'output_channel': data['CueList']['Event'][0]['outputChannel'],
            }
        }

        if eventType == 'song':
            meta['extra_data']['category'] = data['CueList']['Event'][0][eventType.title()]['category']

        return meta

class EFM94(Station):
    _name = '94EFM'
    _slug = '94EFM'

class Get1025(Station):
    _name = 'GET 102.5'
    _slug = 'GET1025'
