import urllib, urllib.parse
import requests
import re
import json
from pyquery import PyQuery # requires module install
from datetime import datetime, timedelta

TRAFFIC_STATS_URL ='/data.lua'

class FritzBoxInternetStats:
    def __init__(self, session_id: str, base_url: str) -> None:
        self.session_id = session_id
        self.url = urllib.parse.urljoin(base_url, TRAFFIC_STATS_URL)

    """gets the internet-stats from yesterday"""
    def get_yesterday(self) -> dict[str, any]:
        netcnt_html = self.__get_netcnt_html()
        stats = self.__get_stats_yesterday(netcnt_html)

        return stats

    """gets the internet-stats html-page from the fritz-box"""
    def __get_netcnt_html(self) -> str:
        headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
        data = {
            'xhr': '1',
            'sid': self.session_id,
            'lang': 'en',
            'no_siderenew': '',
            'page': 'netCnt',
        }

        response = requests.post(self.url, data=data, headers=headers)

        if response.status_code != 200:
            raise Exception(f'unable to retrieve stats site. received status-code "{response.status_code}"')
        
        return response.content
    
    """determines the internet-stats from yesterday from a given html-page"""
    def __get_stats_yesterday(self, html_content: str) -> dict[str, any]:
        sent_and_received = self.__get_sent_and_received_yesterday(html_content)
        connections_and_online_time = self.__get_connections_and_online_time_yesterday(html_content)

        stats_yesterday = {
            'date': datetime.today() - timedelta(1),
            'connections': connections_and_online_time['connections'],
            'online_time': connections_and_online_time['online_time'],
            'megabytes_sent': sent_and_received['sent'],
            'megabytes_received': sent_and_received['received'],
            'megabytes_total': sent_and_received['total']
        }

        return stats_yesterday
    
    """determines the traffic-data from yesterday from the given html-content"""
    def __get_sent_and_received_yesterday(self, html_content: str) -> dict[str, float]:
        # the data for the traffic is hidden inside a JSON in the javascript-code
        # this regex seems to get the job done fairly well: https://regexr.com/7hhib
        match = re.search('(const data = )(?P<json_content>.*)(;)', html_content.decode('utf-8'))
        json_data_str = match.group('json_content')

        json_data = json.loads(json_data_str)
        yesterday = json_data['Yesterday']

        sent_high = int(yesterday['BytesSentHigh'])
        sent_low = int(yesterday['BytesSentLow'])

        received_high = int(yesterday['BytesReceivedHigh'])
        received_low = int(yesterday['BytesReceivedLow'])

        megabytes_sent = self.__calculate_megabytes(sent_high, sent_low)
        megabytes_received = self.__calculate_megabytes(received_high, received_low)
        megabytes_total = megabytes_sent + megabytes_received

        return {
            'sent': megabytes_sent,
            'received': megabytes_received,
            'total': megabytes_total
        }
    
    """determines the connections and online-time from the given html-content"""
    def __get_connections_and_online_time_yesterday(self, html_content: str) -> dict[str, int]:
        query = PyQuery(html_content)

        online_time = query('tr#uiYesterday>td.time')
        connections = query('tr#uiYesterday>td.conn')

        return {
            'online_time': self.__calculate_online_time_in_minutes(online_time.text()),
            'connections': int(connections.text())
        }

    """traffic-data is split in high- and low-bytes and this function calculates the actual megabyte value"""
    def __calculate_megabytes(self, high_bytes: int, low_bytes: int) -> float:
        # 4294967296 = max-limit of uint32
        total_bytes = high_bytes * 4294967296 + low_bytes
        total_megabytes = total_bytes / 1024 / 1024

        return total_megabytes
    
    """the online-time is displayed like 'hh:mm' so this function calculates the total minutes from that string"""
    def __calculate_online_time_in_minutes(self, online_time_str: str) -> int:
        online_time_split = online_time_str.split(':')

        if len(online_time_split) != 2:
            raise Exception('online-time string is not in the right format')

        online_time_in_minutes = int(online_time_split[0]) * 60 + int(online_time_split[1])
        return online_time_in_minutes
