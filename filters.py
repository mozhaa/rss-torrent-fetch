import re
from datetime import datetime
from typing import *


def quality(item: Dict) -> str | None:
    match = re.search('(1080p|720p|480p)', item['title'])
    return match.group(0) if match is not None else None


def subs_group(item: Dict) -> str | None:
    match = re.search('^\[([^\[\]]*)\]', item['title'])
    return match.group(1) if match is not None else None


def episode(item: Dict) -> int | None:
    match = re.search(r'(?: ([0-9]+) |\bE([0-9]+)\b|\bS[0-9]+E([0-9]+)\b)', item['title'])
    if match is None:
        return None
    episode = next((x for x in match.groups() if x is not None), None)
    if episode is None:
        return None
    elif episode.isdigit():
        return int(episode)
    else:
        return None


def basic_filter(item: Dict, last_fetch_time: datetime, params: Dict) -> Tuple[bool, str, Dict]:
    if item['pubdate'] < last_fetch_time:
        return False, f'Publication date {item['pubdate']} < {last_fetch_time} (previous fetch)', params
    item_episode = episode(item)
    item_quality = quality(item)
    item_subs_group = subs_group(item)
    if 'ignore_episodes' in params.keys():
        if item_episode is None:
            return False, f'Failed to figure out episode num', params
        if item_episode in params['ignore_episodes']:
            return False, f'Episode "{item_episode}" in {params['ignore_episodes']}', params
    if 'quality' in params.keys():
        if item_quality not in params['quality']:
            return False, f'Quality "{item_quality}" not in {params['quality']}', params
    if 'subs_group' in params.keys():
        if item_subs_group not in params['subs_group']:
            return False, f'Subs group "{item_subs_group}" not in {params['subs_group']}', params
    if 'additional_regex' in params.keys():
        for regex in params['additional_regex']:
            if re.match(regex, item['title']) is None:
                return False, f'Additional regex "{regex}" did not match', params
    if 'additional_false_regex' in params.keys():
        for regex in params['additional_false_regex']:
            if re.match(regex, item['title']) is not None:
                return False, f'Additional false regex "{regex}" did match', params
    if 'ignore_episodes' in params.keys():
        params['ignore_episodes'].append(item_episode)
    return True, '', params


def erai_raws_1080p_hevc(item: Dict, last_fetch_time: datetime, params: Dict) -> Tuple[bool, str, Dict]:
    params.update({
        'subs_group': [
            'Erai-raws'
        ],
        'quality': [
            '1080p'
        ],
        'additional_regex': [
            '^.*HEVC.*$'
        ]
    })
    return basic_filter(item, last_fetch_time, params)