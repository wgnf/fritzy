import sys
import pymongo # requires module install
from dotenv import load_dotenv # requires module install
import os

from fritzy_auth import FritzBoxAuthenticator
from fritzy_netstats import FritzBoxInternetStats

def execute():
    print(f'python version:     {sys.version_info}')
    print(f'pymongo version:    {pymongo.version} ({pymongo.has_c()})')

    session_id = ''

    try:
        load_dotenv()

        base_url = os.getenv('FRITZ_BASE_URL')
        user = os.getenv('FRITZ_USER')
        password = os.getenv('FRITZ_PASSWORD')

        authenticator = FritzBoxAuthenticator(base_url, user, password)
        session_id = authenticator.auth()

        stats_getter = FritzBoxInternetStats(session_id, base_url)
        stats = stats_getter.get_yesterday()

        print(stats)

        write_stats_to_db(stats)
    except Exception as exception:
        exception_message = str(exception)
        print(exception_message, file=sys.stderr)
    finally:
        if len(session_id) > 0:
            authenticator.logout(session_id)

def write_stats_to_db(traffic_stats: dict[str, any]) -> None:
    mongo_url = os.getenv('MONGO_URL')
    mongo_db = os.getenv('MONGO_DB')
    mongo_collection = os.getenv('MONGO_COLLECTION')

    try:
        print('writing data to db...')
        db_client = pymongo.MongoClient(mongo_url)
        db = db_client[mongo_db]
        collection = db[mongo_collection]
        
        collection.insert_one(traffic_stats)
        print('data successfully written to db')
    except Exception as exception:
        raise Exception('unable to push data to the mongo-db. is your db configured and running?') from exception
