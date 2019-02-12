#!/usr/bin/python
# %%
###############################################################################
## Description
###############################################################################
# Classes and functions for multi-thread processing

###############################################################################
## Imports 
###############################################################################
# check if current path in sys.path; if not, append
import sys
from pathlib import Path
main_folder = Path(__file__).absolute().parent.parent
if not main_folder in sys.path:
    sys.path.append(str(main_folder))

import queue, threading, json, os, time, random
from itertools import cycle, repeat
from functools import partial

import numpy as np
import pandas as pd

from udec.ulogger import create_logger, Udeclogger
from helpers import read_json
# import driver based on config file
config = main_folder.joinpath('data/config.json')
try:
    config = read_json(config)
    if config['favor_browser'] == 'firefox':
        from browsermaster import FirefoxMaster as Driver
    # add elif here if new driver is supported
    else:
        from browsermaster import ChromeMaster as Driver
except (FileNotFoundError, KeyError):
    from browsermaster import ChromeMaster as Driver



###############################################################################
## CONSTANTS & HELPER FUNCTIONS
###############################################################################
stop_flag = 'land'


def read_csv(*args, **kwargs):
    return pd.read_csv(*args, **kwargs)

def read_table(*args, **kwargs):
    return pd.read_table(*args, **kwargs)

def read_excel(*args, **kwargs):
    return pd.read_excel(*args, **kwargs)

def read_json(*args, **kwargs):
    return pd.read_json(*args, **kwargs)

def read_html(*args, **kwargs):
    return pd.read_html(*args, **kwargs)

def read_list(l, *args, **kwargs):
    return pd.DataFrame(l, *args, **kwargs)

VALID_STATUS = ['notready', 'ready', 'paused', 'working', 'done', 'fatal']

# VALID_WORKERS = {
#     'worker':   Workerb,
#     'browser':  Browserb
# }

# flower fetchers
VALID_FLOWERS = {
    'csv':          read_csv,
    'csv-like':     read_table,
    'excel':        read_excel,
    'json':         read_json,
    'html_table':   read_html,
    'list':         read_list
}

try:
    import gspread
    def read_spsht(id_or_url, sname, sp_credential_file, sp_scope, *args, **kwargs):
        try:
            from oauth2client.service_account import ServiceAccountCredentials
            gc = gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name(sp_credential_file, sp_scope))
        except:
            from oauth2client.client import SignedJwtAssertionCredentials
            json_key = json.loads(os.read(os.open(sp_credential_file, os.O_RDONLY),9999999))
            gc = gspread.authorize(SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'].encode(), sp_scope))
        try:
            sp = gc.open_by_key(id_or_url)
        except:
            sp = gc.open_by_url(id_or_url)
        ws = sp.worksheet(sname)
        values = ws.get_all_values()
        return pd.DataFrame(values, *args, **kwargs)
    VALID_FLOWERS['spreadsheet'] = read_spsht
except:
    pass
###############################################################################
## CLASSES
###############################################################################

def bee(b):
    '''Decorator for definitely harmless cute bees ,､’`( ꒪Д꒪),､’`’`,､'''
    b.ID = 0
    original_init = b.__init__
    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        b.ID += 1
        self._id = b.ID
        self.name = str(self._id) if not 'name' in kwargs else kwargs.pop('name')
    def __repr__(self):
        return '{}(name={}, id={})'.format(b.__name__, self.name, self._id)
    def __str__(self):
        return '{} {} #{}'.format(b.__name__, self.name, self._id)
    b.__init__ = __init__
    b.__repr__ = __repr__
    b.__str__ = __str__
    return b

@bee
class Babyb(threading.Thread):

    '''Basic class of all bees'''

    def __init__(self):
        threading.Thread.__init__(self)
        self._status = 'notready'
    
    @property
    def status(self):
        return self._status
    @status.setter
    def status(self, s):
        if not s in VALID_STATUS:
            raise ValueError('Invalid status. Valid values are: {}'.format(', '.join(VALID_STATUS)))
        self._status = s
        self.logger.info('{} {}'.format(str(self), self.status))
    

@bee
class Queenb(Babyb):
    '''Muti-threading manager.

    Queen does all the initialization and management of children threads:
        1. create a queue containing functions and their arguments.
        2. managing containers for workers
        3. managing the processes of works

    args:
        max_children: Max number of threads to create.
        queue_size: Size of the queue.

        func: A callable. Optional, and can be changed/set later.
        constant_args: A list of arguments that are samely used 
            by all workers.
        constant_kwargs: A dict of keyword arguments that are 
            samely used by all workers.
        variable_args: A list of arguments that are used one by 
            one by workers.
        variable_kwargs: A dict of arguments that are used one 
            by one by workers. 
            The keys are argument names.
            The values are lists of argument names. 
            When given, the lists must be same length as 
            `variable_args` if it's given.
    '''

    def __init__(self, max_children=7, queue_size=0, queueb_name='QB', queueb_interval=5, killerb_name='Agent 47', killerb_interval=10, logger=None, *args, **kwargs):
        Babyb.__init__(self)
        self.logger = create_logger(name='HIVEMIND', filepath='queen.log') if logger is None else logger
        # multi-threading lock and queue
        self.lock = threading.Lock()
        self.queue = queue.Queue(queue_size)
        # init children
        self.max_children = 4 if max_children < 4 else max_children
        self.honeybs = [] # retrievers 
        self.workerbs = [] # consumers

        self.qb = self.add_child(Queueb, name=queueb_name, sleep_interval=queueb_interval)
        self.killerb = self.add_child(Killerb, name=killerb_name, sleep_interval=killerb_interval)
        # self.reset_killerb(killer_interval)

        self.results = []
        self.done = False
        self.status = 'ready'
    
    @Udeclogger(ltype='excexe')
    def add_child(self, child, *args, **kwargs):
        if self.count('worker') + self.count('honey') < self.max_children:
            b = child(self, *args, **kwargs)
            return b
        else:
            self.logger.warning('Hive is full.')


    # @Udeclogger(ltype='excexe')
    # def add_honeyb(self, *args, **kwargs):
    #     if self.count('worker') + self.count('honey') < self.max_children:
    #         honeyb = Honeyb(self, *args, **kwargs)
    #         return honeyb
    
    # @Udeclogger(ltype='excexe')
    # def add_workerb(self, *args, **kwargs):
    #     if self.count('worker') + self.count('honey') < self.max_children:
    #         workerb = Workerb(self, *args, **kwargs)
    #         return workerb
    #     else:
    #         self.logger.info('Hive is full.')

    # @Udeclogger(ltype='excexe')
    # def reset_killerb(self, sleep_interval=10, **kwargs):
    #     # print(self, sleep_interval, kwargs)
    #     self.killerb = Killerb(self, name='Agent 47', sleep_interval=sleep_interval)


    def count(self, btype):
        if btype == 'honey':
            return len(self.honeybs)
        else:
            return len(self.workerbs)

    @Udeclogger(ltype='execution')
    def add_to_queue(self, iterable, sleep=3, **kwargs):
        for i in iterable:
            while True:
                if self.status == 'done':
                    break
                try:
                    self.lock.acquire()
                    self.queue.put_nowait(i)
                except queue.Full:
                    self.lock.release()
                    time.sleep(sleep)
                    continue
                else:
                    self.lock.release()
                    break

    @Udeclogger(ltype='execution')
    def add_stop_flag(self, sleep=3, **kwargs):
        self.add_to_queue([stop_flag for _ in range(self.count('workerb'))], sleep=sleep, suppress=True)
            
    @Udeclogger(ltype='execution')
    def fetch_one(self, sleep=3, **kwargs):
        try:
            self.lock.acquire()
            raw = self.queue.get_nowait()
        except queue.Empty:
            self.lock.release()
            raise
        self.lock.release()
        return raw
    
    @Udeclogger(ltype='excexe')
    def add_result(self, r, **kwargs):
        self.results.append(r)

    @Udeclogger(ltype='excexe')
    def export_result(self, func=None, **kwargs):
        if not func is None:
            func(self.results)
        else:
            pass # save to csv
    
    # processing without honeyb
    def process(self, child, func, func_args, *child_args, **child_kwargs):
        child = self.add_child(child, *child_args, **child_kwargs)
        self.qb.add_to_queue([func, func_args])
        if child:
            child.start()

    def run(self):
        # Queen ready; doing check
        #  honey all function and variables set, ready
        #  workers, qb, killerb exists, ready
        # then Queen working, start everything

        # checking if honeyb ready
        self.status = 'working'
        self.killerb.start()
        ready_honeyb = 0
        while ready_honeyb == 0:
            for b in self.honeybs:
                if b.status == 'ready':
                    ready_honeyb += 1
                b.start()
            self.logger.info('{} honeyb(s) are ready.{}'.format(ready_honeyb, '' if ready_honeyb==0 else ' Start working...'))
        
        for b in self.workerbs:
            b.start()
        while self.count('worker') + self.count('honey') < self.max_children:
            if not self.queue.empty():
                b = self.add_child(Workerb)
                b.start()
            elif sum([b.status == 'working' for b in self.honeybs]) == 0:
                break
        # add end flags
        self.add_stop_flag(prefix=str(self)+' -- ')
        for b in self.workerbs:
            b.join()
        self.rest()
    
    @Udeclogger(ltype='excexe')
    def pause(self, **kwargs):
        self.lock.acquire()
        self.status = 'paused'

    @Udeclogger(ltype='excexe')
    def resume(self, **kwargs):
        self.lock.release()
        self.status = 'working'

    @Udeclogger(ltype='excexe')
    def rest(self, **kwargs):
        self.done = True
        if self.status != 'done':
            self.status = 'done'
            self.killerb.bury()
            self.killerb.clear()
    
    @Udeclogger(ltype='excexe')
    def kill(self, **kwargs):
        self.status = 'fatal'
        for b in self.honeybs:
            b.status = 'fatal'
        for b in self.workerbs:
            b.status = 'fatal'
        self.killerb.bury()
        self.killerb.clear()

@bee
class Queueb(Babyb):
    
    '''Manager of Queen's queue.'''

    def __init__(self, queen, sleep_interval=5, *args, **kwargs):
        Babyb.__init__(self)
        
        self.Queen = queen
        self.lock = self.Queen.lock
        self.queue = self.Queen.queue
        self.logger = self.Queen.logger

        self.sleep = sleep_interval
        self.status = 'ready'

        self.queue_ready = False
    
    @Udeclogger(ltype='execution')
    def add_one(self, one, *args, **kwargs):
        while True:
            if self.Queen.status == 'done':
                break
            try:
                self.lock.acquire()
                self.queue.put_nowait(one)
            except queue.Full:
                self.lock.release()
                time.sleep(self.sleep)
                continue
            else:
                self.lock.release()
                break

    @Udeclogger(ltype='execution')
    def add_to_queue(self, iterable, **kwargs):
        for i in iterable:
            self.add_one(i, suppress=True)

    @Udeclogger(ltype='execution')
    def add_stop_flag(self, **kwargs):
        self.add_to_queue([stop_flag for _ in range(self.Queen.count('workerb'))], sleep=self.sleep, suppress=True)
    
    @Udeclogger(ltype='execution')
    def fetch_one(self, *args, **kwargs):
        try:
            self.lock.acquire()
            raw = self.queue.get_nowait()
        except queue.Empty:
            self.lock.release()
            raise
        self.lock.release()
        return raw
    
    def run(self):
        # check if Queen working
        self.status = 'working'
        if self.Queen.status == 'working':
            while True:
                time.sleep(self.sleep)
                if self.queue.empty():
                    if self.Queen.status == 'done':
                        self.logger.info('{} -- queue is cleared; job done.'.format(str(self)))
                        break
                    elif self.Queen.honeybs: # if any honeyb exists
                        for h in self.Queen.honeybs:
                            if h.status != 'done': # if any honeyb is still working
                                self.logger.info('{} -- queue is empty.'.format(str(self)))
                                self.queue_ready = False
                                continue
                    else: # no honeybs, instruct workers to stop
                        self.add_stop_flag(prefix=str(self)+' -- ')
                        continue
                else:
                    if not self.queue_ready:
                        self.logger.info('{} -- queue is filled.'.format(str(self)))
                        self.queue_ready = True
        self.status = 'done'
     

@bee
class Honeyb(Babyb):
    '''Fetch functions and variables, and push into queue

    3 steps:
        1. read data from valid inputs;
        2. get functions that pre-process the data;
        3. push functions and data into Queen's queue row by row.
    '''

    def __init__(self, queen, flower=None, fetch_args=[], fetch_kwargs={}, rough_func=None, rough_args=[], rough_kwargs={}, work_func=None, work_args=[], work_kwargs={}, sleep_interval=3, *args, **kwargs):
        Babyb.__init__(self)
        
        self.Queen = queen
        self.Queen.honeybs.append(self)
        self.logger = self.Queen.logger
        
        self.sleep = sleep_interval

        self.raw_pollen = None
        self.roughed_pollen = None

        
        self.collected = False
        self.func_set = False
        self._ready = [self.collected, self.func_set]

        self.collect(flower, prefix=str(self)+' -- ', *fetch_args, **fetch_kwargs)
        self.rough(rough_func, prefix=str(self)+' -- ', *rough_args, **rough_kwargs)
        self.set_work_func(work_func, prefix=str(self)+' -- ', *work_args, **work_kwargs)
        
        self.done = False

    @property
    def ready(self):
        return self._ready
    @ready.setter
    def ready(self, l):
        self._ready = l
        if sum(self._ready) == 2:
            self.status = 'ready'
    
    @Udeclogger(ltype='exception', re_raise=False)
    def collect(self, flower, *args, **kwargs):
        self.logger.info('{} -- collecting pollen...'.format(self))
        if flower not in VALID_FLOWERS:
            raise ValueError('Invalid flower. Check help string for valid flowers.')
        self.raw_pollen = VALID_FLOWERS[flower](*args, **kwargs)
        self.collected = True
        self.ready = [self.collected, self.func_set]
        self.logger.info('{} -- done collecting.'.format(self))
    
    @Udeclogger(ltype='exception', re_raise=False)
    def rough(self, rough_func, *args, **kwargs):
        self.logger.info('{} -- pre-processing pollen...'.format(self))
        self.roughed_pollen = self.raw_pollen if rough_func is None else rough_func(self.raw_pollen, *args, **kwargs)
        self.logger.info('{} -- done pre-processing.'.format(self))

    @Udeclogger(ltype='exception', re_raise=False)
    def set_work_func(self, func, *args, **kwargs):
        self.logger.info('{} -- preparing working-function...'.format(self))
        self.work_func = partial(func, *args, **kwargs)
        self.logger.info('{} -- done preparing.'.format(self))
        self.func_set = True
        self.ready = [self.collected, self.func_set]

    def run(self):
        '''Store pre-processed data to Queen's queue.'''
        if self.status == 'ready':
            self.status = 'working'
            if self.Queen.status == 'working':
                # save original data into Queen
                self.Queen.origin_data = self.roughed_pollen
                # push data into queue
                self.Queen.qb.add_to_queue(zip(repeat(self.work_func), self.roughed_pollen.itertuples()), self.sleep, prefix=str(self)+' -- ')
        else:
            self.logger.warning('{} not ready. Exit'.format(str(self)))
        self.status = 'done'

@bee
class Workerb(Babyb):

    def __init__(self, queen, sleep_interval=6, *args, **kwargs):
        Babyb.__init__(self)

        self.Queen = queen
        self.Queen.workerbs.append(self)
        self.logger = self.Queen.logger

        self.sleep = sleep_interval

        self.status = 'ready'

        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        '''Get one function and a bunch of data, and run the function, from queue.'''
        self.status = 'working'
        if self.Queen.status == 'working':
            while True:
                # check if queue is ready
                if self.Queen.qb.queue_ready:
                    try:
                        raw = self.Queen.fetch_one(self.sleep, prefix=str(self)+' -- ')
                    except queue.Empty:
                        self.logger.info('{} -- empty queue.'.format(self))
                        time.sleep(self.sleep)
                        continue
                    if raw == stop_flag:
                        break
                    
                    func, args = raw
                    idx = args[0]
                    args = args[1:]
                    try:
                        r = func(*args, prefix=str(self)+' -- ', *self.args, **self.kwargs)
                    except Exception as e:
                        self.logger.critical(e)
                        raise
                    
                    self.Queen.add_result([idx, func, args, r], prefix=str(self)+' -- ')
        self.status = 'done'

@bee
class Browserb(Workerb):

    def __init__(self, queen, driver='chrome', sleep_interval=6, quit_on_error=True, *args, **kwargs):
        Workerb.__init__(self, queen, sleep_interval, *args, **kwargs)

        self.quit_on_error = quit_on_error
        self.driver = Driver()
    
    def run(self):
        '''Get one function and a bunch of data, and run the function, from queue, with browser-automation'''
        self.status = 'working'
        if self.Queen.status == 'working':
            while True:
                # check if queue is ready
                if self.Queen.qb.queue_ready:
                    try:
                        raw = self.Queen.fetch_one(self.sleep, prefix=str(self)+' -- ')
                    except queue.Empty:
                        self.logger.info('{} -- empty queue.'.format(self))
                        time.sleep(self.sleep)
                        continue
                    if raw == stop_flag:
                        break
                    
                    # when using Browserb, the func must accept a `driver` keyword argument
                    func, args = raw
                    idx = args[0]
                    args = args[1:]
                    try:
                        r = func(*args, driver=self.driver, prefix=str(self)+' -- ', *self.args, **self.kwargs)
                    except Exception as e:
                        self.logger.critical(e)
                        if self.quit_on_error:
                            self.driver.quit()
                        raise
                    
                    self.Queen.add_result([idx, func, args, r], prefix=str(self)+' -- ')
        self.driver.quit()
        self.status = 'done'
        
@bee
class Killerb(Babyb):

    def __init__(self, queen, sleep_interval=10, *args, **kwargs):
        Babyb.__init__(self)
        self.Queen = queen
        self.sleep = sleep_interval
        self.logger = self.Queen.logger

    @Udeclogger(ltype='execution')
    def clear(self, **kwargs):
        self.Queen.lock.acquire()
        while True:
            try:
                self.Queen.queue.get_nowait()
            except queue.Empty:
                self.Queen.lock.release()
                break
        if self.Queen.workerbs:
            self.Queen.add_stop_flag(prefix=str(self)+' -- ')
    
    def bury(self):
        for i in range(self.Queen.count('honey')-1, -1, -1):
            if self.Queen.honeybs[i].status in ['done', 'fatal']:
                del self.Queen.honeybs[i]
        for i in range(self.Queen.count('worker')-1, -1, -1):
            if self.Queen.workerbs[i].status in ['done', 'fatal']:
                del self.Queen.workerbs[i]

    def run(self):
        self.status = 'working'
        while True:
            if self.Queen.status == 'done' and self.Queen.count('worker') + self.Queen.count('honey') == 0:
                break
            self.bury()
            time.sleep(self.sleep)
        self.status = 'done'

# %%
if __name__ == '__main__':
    def temp(*x, **kwargs):
        print(sum(x))
        time.sleep(random.randint(1,5))
    logger = create_logger(name='QueenTest', filepath='test.log', stdout=True)
    q = Queenb(max_children=5, queue_size=10, logger=logger)
    h = q.add_honeyb(flower='list', fetch_args=[list(zip(range(10),range(10,20)))], work_func=temp)
    for _ in range(3):
        q.add_workerb()
    q.start()