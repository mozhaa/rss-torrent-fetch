import configparser
import httpx
import time
import json
import logging
from datetime import datetime
from functools import partial
import xml.etree.ElementTree as et

from torrents import *
from filters import *


class QBitTorrentAuth(httpx.Auth):
    def __init__(self, host: str, port: str, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sid = None
        self.logger = logging.getLogger('QBitTorrentAuth')
    
    def obtain_sid(self):
        self.logger.info('Obtaining SID...')
        params = {'username': self.username, 'password': self.password}
        auth_url = f'{self.host}:{self.port}/api/v2/auth/login'
        response = yield httpx.Request(method='POST', url=auth_url, params=params)
        if response.status_code != 200:
            self.logger.error(f'Obtaining SID failed with status code {response.status_code}')
            with open('error.log', 'w+') as f:
                f.write(response.text)
            raise RuntimeError(f'Authentication failed! Error message can be found in error.log')
        self.sid = response.cookies['SID']
        self.logger.info(f'Successfully obtained SID = {self.sid}')

    def auth_flow(self, request):
        if self.sid is None:
            self.obtain_sid()
        request.cookies['SID'] = self.sid
        yield request

class Fetcher:
    def __init__(self, host: str, port: str, username: str, password: str):
        self.host = host
        self.port = port
        self.auth = QBitTorrentAuth(host, port, username, password)
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
        self.torrent_webclient = httpx.Client(auth=self.auth, headers=headers)
        self.tosho_client = httpx.Client(headers=headers)
        
        self.last_fetch_time = datetime.min
        self.logger = logging.getLogger('Fetcher')
    
    def fetch(self, resources_fp):
        with open(resources_fp, 'r') as f:
            resources = json.load(f)
        for resource in resources:
            filter = partial(globals()[resource['filter']['name']], params=resource['filter']['params'])
            response = self.tosho_client.get(resource['rss_url'])
            tree = et.fromstring(response.text)
            for node in tree.findall('./channel/item'):
                item = TorrentItem(node)
                accepted, reason, new_params = filter(item=item, last_fetch_time=self.last_fetch_time)
                if accepted:
                    self.logger.info(f'Item "{item.title}" accepted.')
                else:
                    self.logger.info(f'Item "{item.title}" rejected. Reason: {reason}')
                resource['filter']['params'] = new_params
            self.last_fetch_time = datetime.now()
        with open(resources_fp, 'w') as f:
            json.dump(resources, f)
                    

def main():
    config = configparser.ConfigParser()
    config.read('fetch.config')
    
    fetcher = Fetcher(
        host=config['torrent']['host'],
        port=config['torrent']['port'],
        username=config['torrent']['username'],
        password=config['torrent']['password']
    )
    
    while True:
        fetcher.fetch(resources_fp=config['fetch']['resources_fp'])
        time.sleep(int(config['fetch']['fetch_interval']))

if __name__ == '__main__':
    main()