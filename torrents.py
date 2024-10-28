from abc import abstractmethod
from typing import *
from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as et

@dataclass
class TorrentItem:
    title: str
    url: str
    pubdate: datetime

class Torrent:
    @abstractmethod
    def items(self, rss) -> List[TorrentItem]:
        pass

class AnimeTosho(Torrent):
    def items(self, rss) -> List[TorrentItem]:
        tree = et.fromstring(rss)
        items = []
        for item in tree.findall('./channel/item'):
            t = TorrentItem()
            t.title = item.find('title').text
            t.url = item.find('enclosure').get('url')
            t.pubdate = datetime.strptime(item.find('pubDate').text, '%a, %d %b %Y %H:%M:%S %z')
            items.append(t)
        return items
        