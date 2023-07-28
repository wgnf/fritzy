from scheduler import Scheduler
from fritzy import execute as fritzy_execute
import time
import datetime as dt

def main():
    scheduler = Scheduler()
    
    scheduler.daily(dt.time(hour=3), execute_fritzy)

    print('starting execution with scheduler...')
    while True:
        scheduler.exec_jobs()
        time.sleep(10)


def execute_fritzy():
    print(f'executing fritzy at {dt.datetime.now()}...')
    fritzy_execute()

if __name__ == '__main__':
    main()