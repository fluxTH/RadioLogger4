import requests
from urllib.parse import quote_plus

class YahooProxyException(Exception):
    pass

class YahooProxy():
    ENDPOINT = 'https://query.yahooapis.com/v1/public/yql?format=json&q={query}'
    def __init__(self):
        pass

    def send_query(self, query):
        target = self.ENDPOINT.format(query=quote_plus(query))
        #print(target)
        req = requests.get(target, timeout=10)
        return req.json()

    def get_html(self, url):
        q = "select * from html where url='{}'".format(url)
        result = self.send_query(q)
        if result['query']['count'] > 0:
            return result['query']['results']['body']

        return False

    def get_json(self, url):
        q = "select * from json where url='{}'".format(url)
        result = self.send_query(q)
        if result['query']['count'] > 0:
            return result['query']['results']['json']

        return False

    def get_xml(self, url):
        q = "select * from xml where url='{}'".format(url)
        result = self.send_query(q)
        if result['query']['count'] > 0:
            return result['query']['results']

        return False

    def post(self, url, data):
        pass
