import configparser
import httpx
import time
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from functools import partial
from termcolor import colored

from torrents import *
from filters import *


class QBitTorrentClient:
    def __init__(self, url: str, params: Dict):
        self.url = url
        self.params = params
    
    def add_torrent(self, url: str):
        data = {'urls': [url]}
        data.update(self.params)
        httpx.post(f'{self.url}/api/v2/torrents/add', data=data)


class Fetcher:
    def __init__(self, qbt_client: QBitTorrentClient):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
        self.tosho_client = httpx.Client(headers=headers)
        self.last_fetch_time = datetime.min.replace(tzinfo=ZoneInfo('UTC'))
        self.qbt_client = qbt_client
    
    def fetch(self, resources_fp):
        with open(resources_fp, 'r') as f:
            resources = json.load(f)
        for resource in resources:
            print(colored(f'Fetching resource: "{resource['rss_url']}"', 'white'))
            response = self.tosho_client.get(resource['rss_url'])
            
            filter = partial(globals()[resource['filter']['name']], params=resource['filter']['params'])
            items = globals()[resource['torrent']](response.text)
            for item in items:
                accepted, reason, new_params = filter(item=item, last_fetch_time=self.last_fetch_time)
                if accepted:
                    print(colored(f'\t"{item['title']}" accepted.', 'green'))
                    self.qbt_client.add_torrent(item['url'])
                else: 
                    if 'Publication date' not in reason:
                        print(colored(f'\t"{item['title']}" rejected.\n\t\tReason: {reason}', 'yellow'))
                resource['filter']['params'] = new_params
        with open(resources_fp, 'w') as f:
            json.dump(resources, f, indent=4)
        self.last_fetch_time = datetime.now().astimezone()
      
                    
def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    qbt_client = QBitTorrentClient(
        url=config['torrent']['url'],
        params=config['qbittorrent parameters']
    )
    
    fetcher = Fetcher(qbt_client)
    
    while True:
        fetcher.fetch(resources_fp=config['fetch']['resources_fp'])
        time.sleep(int(config['fetch']['fetch_interval']))


if __name__ == '__main__':
    main()