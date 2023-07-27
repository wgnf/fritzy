import argparse
import requests # requires a module install
import sys
import xml.etree.ElementTree as ET
import hashlib
import urllib, urllib.parse
import re
import json
from datetime import datetime, timedelta
from pyquery import PyQuery # requires module install
import pymongo # requires module install

LOGIN_URL = "/login_sid.lua?version=2"
TRAFFIC_STATS_URL ="/data.lua"

# TODO: better error handling using exceptions instead of sys.exit!
# TODO: remove excessive prints
# TODO: improve code-structure
# TODO: respect the "BlockTime"
# TODO: sanity checks i.e. when splitting strings
# TODO: handle secrets better

def main():
    args = get_args()
    box_login_url = urllib.parse.urljoin(args["url"], LOGIN_URL)

    challenge_response = get_challenge_response(box_login_url, args["password"])
    session_id = get_session_id(challenge_response, args["user"], box_login_url)

    traffic_stats = get_traffic_stats_yesterday(session_id, args["url"])
    print(traffic_stats)

    write_traffic_stats_to_db(traffic_stats)

    # TODO: this should always be executed even when an exception occurs after we established a session
    logout(session_id, args["user"], box_login_url)

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

def get_challenge_response(box_login_url: str, password: str) -> str:
    # have a look at this document to see whats going on here: https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/AVM_Technical_Note_-_Session_ID_english_2021-05-03.pdf
    response = requests.get(box_login_url)

    if response.status_code != 200:
        print(f"Error while requesting login-information: {response.status_code}")
        sys.exit(1)

    login_challenge = get_challenge_from_xml(response.content)
    challenge_tokens = get_tokens_from_challenge(login_challenge)

    print(f"tokens: {challenge_tokens}")

    if challenge_tokens["version"] != '2':
        print(f"Login version '{challenge_tokens['version']}' is not supported (yet)")
        sys.exit(2)

    hash1 = pbkdf2_hex(password.encode(), challenge_tokens["salt1"], challenge_tokens["iter1"])
    hash2 = pbkdf2_hex(hash1, challenge_tokens["salt2"], challenge_tokens["iter2"])
    
    challenge_response_str = f"{challenge_tokens['salt2'].hex()}${hash2.hex()}"
    print(challenge_response_str)
    return challenge_response_str

def get_session_id(challenge_response: str, user: str, box_login_url: str) -> str:
    request_data_dict = { 
        "username": user, 
        "response": challenge_response 
    }

    post_data = urllib.parse.urlencode(request_data_dict).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    post_response = requests.post(box_login_url, post_data, headers=headers)

    if post_response.status_code != 200:
        print(f"Error while requesting session-id: {post_response.status_code}")
        sys.exit(3)

    xml_tree = ET.ElementTree(ET.fromstring(post_response.content))
    xml_root = xml_tree.getroot()
    session_id = xml_root.find("SID").text

    print(session_id)

    if session_id == "0000000000000000":
        print("The returned session-id is not valid")
        sys.exit(4)

    print(f"session-id: {session_id}")
    return session_id

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

def logout(session_id: str, user: str, box_login_url: str) -> None:
    logout_data_dict = { 
        "username": user, 
        "sid": session_id,
        "logout": 1
    }

    post_data = urllib.parse.urlencode(logout_data_dict).encode()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    post_response = requests.post(box_login_url, post_data, headers=headers)

    if post_response.status_code != 200:
        print(f"Error while logging out: {post_response.status_code}")
        sys.exit(6)

    print("logged out.")

def get_challenge_from_xml(xml_str: str) -> str:
    xml_tree = ET.ElementTree(ET.fromstring(xml_str))
    xml_root = xml_tree.getroot()
    challenge = xml_root.find("Challenge").text

    if len(challenge) < 1:
        print("Could not find challenge in response")
        sys.exit(99)

    return challenge

def get_tokens_from_challenge(challenge: str) -> dict[str, any]:
    challenge_split = challenge.split("$")
    challenge_tokens = {
        "version": challenge_split[0],
        "iter1": int(challenge_split[1]),
        "salt1": bytes.fromhex(challenge_split[2]),
        "iter2": int(challenge_split[3]),
        "salt2": bytes.fromhex(challenge_split[4])
    }

    return challenge_tokens

def pbkdf2_hex(password_bytes: bytes, salt: bytes, iterations: int) -> bytes:
    hashed_password = hashlib.pbkdf2_hmac('sha256', password_bytes, salt, iterations)
    return hashed_password

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
