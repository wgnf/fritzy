import argparse
import sys
import pymongo # requires module install

from fritzy_auth import FritzBoxAuthenticator
from fritzy_netstats import FritzBoxInternetStats

TRAFFIC_STATS_URL ="/data.lua"

# TODO: handle secrets better

def main():
    args = get_args()

    try:
        authenticator = FritzBoxAuthenticator(args['url'], args['user'], args['password'])
        session_id = authenticator.auth()

        stats_getter = FritzBoxInternetStats(session_id, args['url'])
        stats = stats_getter.get_yesterday()

        print(stats)

        write_traffic_stats_to_db(stats)
    except Exception as exception:
        exception_message = str(exception)
        print(exception_message, file=sys.stderr)
    finally:
        if len(session_id) > 0:
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

def write_traffic_stats_to_db(traffic_stats: dict[str, any]) -> None:
    db_client = pymongo.MongoClient("mongodb://localhost:27017")
    db = db_client["fritzy"]
    collection = db["trafficstats"]
    
    collection.insert_one(traffic_stats)

if __name__ == '__main__':
    main()
