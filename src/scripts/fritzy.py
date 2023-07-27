import argparse
import requests # requires a module install
import sys
import xml.etree.ElementTree as ET
import urllib, urllib.parse
import re
import json
from datetime import datetime, timedelta
from pyquery import PyQuery # requires module install
import pymongo # requires module install

from fritzy_auth import FritzBoxAuthenticator

TRAFFIC_STATS_URL ="/data.lua"

# TODO: better error handling using exceptions instead of sys.exit!
# TODO: remove excessive prints
# TODO: improve code-structure
# TODO: sanity checks i.e. when splitting strings
# TODO: handle secrets better

def main():
    args = get_args()

    authenticator = FritzBoxAuthenticator(args['url'], args['user'], args['password'])
    session_id = authenticator.auth()

    traffic_stats = get_traffic_stats_yesterday(session_id, args["url"])
    print(traffic_stats)

    write_traffic_stats_to_db(traffic_stats)

    # TODO: this should always be executed even when an exception occurs after we established a session
    authenticator.logout(session_id)

def get_args() -> dict[str, str]:
    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument("-a", "--address", dest="url", required=False, default="http://fritz.box/", help="the base-url of the fritz-box to query. defaults to 'http://fritz.box/'")
    argument_parser.add_argument("-u", "--user", dest="user", required=True, help="the username of the user to use to login")
    argument_parser.add_argument("-p", "--password", dest="password", required=True, help="the password of the user to login")

    arguments = argument_parser.parse_args()

    args = {
        "url": arguments.url,
        "user": arguments.user,
        "password": arguments.password
    }
    return args

def get_traffic_stats_yesterday(session_id: str, box_url: str) -> dict[str, any]:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "xhr": "1",
        "sid": session_id,
        "lang": "en",
        "no_siderenew": "",
        "page": "netCnt"
    }

    traffic_stats_url = urllib.parse.urljoin(box_url, TRAFFIC_STATS_URL)
    response = requests.post(traffic_stats_url, data=data, headers=headers)

    if response.status_code != 200:
        print(f"Could not request webinterfaces online-counter {response.status_code}")
        sys.exit(5)

    html_content = response.content

    sent_received_yesterday = get_sent_received_yesterday(html_content)
    connections_online_time_yesterday = get_connections_online_time_yesterday(html_content)

    traffic_stats_yesterday = {
        "date": datetime.today() - timedelta(1),
        "connections": connections_online_time_yesterday["connections"],
        "online_time": connections_online_time_yesterday["online_time"],
        "megabytes_sent": sent_received_yesterday["sent"],
        "megabytes_received": sent_received_yesterday["received"],
        "megabytes_total": sent_received_yesterday["total"]
    }

    return traffic_stats_yesterday

def write_traffic_stats_to_db(traffic_stats: dict[str, any]) -> None:
    db_client = pymongo.MongoClient("mongodb://localhost:27017")
    db = db_client["fritzy"]
    collection = db["trafficstats"]
    
    collection.insert_one(traffic_stats)

def get_sent_received_yesterday(html_content: str) -> dict[str, float]:
    # the data for the traffic is hidden inside a JSON in the javascript-code
    # this regex seems to get the job done fairly well: https://regexr.com/7hhib
    match = re.search("(const data = )(?P<json_content>.*)(;)", html_content.decode("utf-8"))
    json_data_str = match.group("json_content")

    print(json_data_str)

    json_data = json.loads(json_data_str)
    yesterday = json_data["Yesterday"]

    sent_high = int(yesterday["BytesSentHigh"])
    sent_low = int(yesterday["BytesSentLow"])

    received_high = int(yesterday["BytesReceivedHigh"])
    received_low = int(yesterday["BytesReceivedLow"])

    megabytes_sent = calculate_megabytes(sent_high, sent_low)
    megabytes_received = calculate_megabytes(received_high, received_low)
    megabytes_total = megabytes_sent + megabytes_received

    return {
        "sent": megabytes_sent,
        "received": megabytes_received,
        "total": megabytes_total
    }

def get_connections_online_time_yesterday(html_content: str) -> dict[str, int]:
    query = PyQuery(html_content)
    
    online_time = query("tr#uiYesterday>td.time")
    connections = query("tr#uiYesterday>td.conn")

    return {
        "online_time": calculate_online_time_in_minutes(online_time.text()),
        "connections": int(connections.text())
    }

def calculate_megabytes(high_bytes: int, low_bytes: int) -> float:
    # 4294967296 = max-limit of uint32
    total_bytes = high_bytes * 4294967296 + low_bytes
    total_megabytes = total_bytes / 1024 / 1024

    return total_megabytes

# the original value is formatted like "hh:mm", so we have to calculate the actual value
def calculate_online_time_in_minutes(online_time_str: str) -> int:
    online_time_split = online_time_str.split(":")

    online_time_in_minutes = int(online_time_split[0]) * 60 + int(online_time_split[1])
    return online_time_in_minutes

if __name__ == '__main__':
    main()
