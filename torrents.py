from typing import *
from datetime import datetime
import xml.etree.ElementTree as et

def anime_tosho(rss) -> List[Dict]:
    return [
        {
            'title': node.find('title').text,
            'url': node.find('enclosure').get('url'),
            'pubdate': datetime.strptime(node.find('pubDate').text, '%a, %d %b %Y %H:%M:%S %z'),
        }
        for node in et.fromstring(rss).findall('./channel/item')    
    ]
