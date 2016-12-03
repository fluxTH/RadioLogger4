#!/usr/bin/python3
#-*- coding: utf-8 -*-

# TODO: log purge

###########################################################
# App
###########################################################
VERSION = '4.0'
DAEMON = False


###########################################################
# Functions
###########################################################
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def _p(s, c=""):
    if not DAEMON:
        if c == "":
            print(s)
        elif c == "head":
            print(bcolors.HEADER + s + bcolors.ENDC)
        elif c == "bold":
            print(bcolors.BOLD + s + bcolors.ENDC)
        elif c == "green":
            print(bcolors.OKGREEN + s + bcolors.ENDC)
        elif c == "blue":
            print(bcolors.OKBLUE + s + bcolors.ENDC)
        elif c == "warn":
            print(bcolors.WARNING + s + bcolors.ENDC)
        elif c == "err":
            print(bcolors.FAIL + s + bcolors.ENDC)

def _(module, s, c=""):
    _p('[{}] ({}) {}'.format(datetime.datetime.now().strftime('%H:%M:%S'), module, s), c=c)

import json
import datetime

def _logToDb(module, message, data=None, priority='Debug'):
    dbsess = Session()
    log = Log(priority=priority, message=message, module=module)
    log.add_data(data)
    dbsess.add(log)
    dbsess.commit()

def _l(module, s, data=None, console=True, save=True):
    if save:
        _logToDb(module, s, data=data, priority='Debug')

    if console:
        _(module, s)

def _w(module, s, data=None, console=True, save=True):
    if save:
        _logToDb(module, s, data=data, priority='Warning')

    if console:
        _(module, s, c='warn')

def _e(module, s, data=None, console=True, save=True):
    if save:
        _logToDb(module, s, data=data, priority='Error')

    if console:
        _(module, s, c='err')


###########################################################
# Main Loop
###########################################################
import os
import sys

if __name__ == "__main__":
    PID = os.getpid()

    if len(sys.argv) > 1 and sys.argv[1] == 'daemon':
        print('\nRunning as DAEMON mode! Send SIGTERM to PID {} to quit.'.format(PID))
        DAEMON = True

    _p('Radio Logger v{} by fluxth'.format(VERSION), c='head')
    _p('+ Starting on PID: {}'.format(PID), c='green')

    ###########################################################
    # DB CONNECTION
    ###########################################################
    import sqlalchemy
    from sqlalchemy.orm import sessionmaker

    DB_STRING = 'sqlite:///log4.db'
    # DB = 'mysql://'
    _l('Core', "Connecting to database '{}'".format(DB_STRING), save=False)
    engine = sqlalchemy.create_engine(DB_STRING) # , echo=True)
    Session = sessionmaker(bind=engine)

    from model import (
        Base,
        Station,
        Asset,
        Play,
        Log,
    )

    # TODO: Check more table other than logs
    if not engine.dialect.has_table(engine, Log.__tablename__):
        _w('DB', 'No database table found, creating...', save=False)
        Base.metadata.create_all(engine)
        _l('DB', 'Table creation successful!')

    _l('Core', 'Radio Logger v{} started using PID {}'.format(VERSION, PID), console=False)

    ###########################################################
    # Station configuration
    ###########################################################
    from station import (
        Cool93,
        Greenwave1065,
        EFM94,
        Get1025,
        EDS885,
    )

    stations = [
        Cool93(engine=engine, log=_, dblog=_logToDb),
        Greenwave1065(engine=engine, log=_, dblog=_logToDb),
        EDS885(engine=engine, log=_, dblog=_logToDb),
        # EFM94(engine=engine, log=_, dblog=_logToDb),
        # Get1025(engine=engine, log=_, dblog=_logToDb),    
    ]

    _l('Core', 'Enabled stations ({}): {}'.format(len(stations), ', '.join(s._name for s in stations)))
    _l('Core', 'Radio Logger v{} Initialized'.format(VERSION))

    import time
    try:
        while True:
            for station in stations:
                if station.run():
                    # if ran
                    pass

            time.sleep(1)

    except KeyboardInterrupt:
        _e('Core', 'SIGTERM received, Terminating!')

    _w('Core', 'End of program, Exiting.')
    sys.exit(0)
