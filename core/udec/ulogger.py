#!/usr/bin/python

###############################################################################
## Description
###############################################################################

###############################################################################
## Imports 
###############################################################################
import logging, sys
from functools import wraps, partial
from pathlib import Path
from inspect import isclass

###############################################################################
## CONSTANTS & HELPER FUNCTIONS
###############################################################################
LEVELS = {
    'critical': logging.CRITICAL,
    'error':    logging.ERROR,
    'warning':  logging.WARNING,
    'info':     logging.INFO,
    'debug':    logging.DEBUG
}

def create_logger(name='UsefulLogger', level='info', filepath='ulog.log', stdout=False, extra_handlers=[], width=80):
    '''
    Creates a logging object and returns it
    '''
    logger = logging.getLogger(name)
    if logger.hasHandlers(): logger.handlers.clear()
    logger.setLevel(LEVELS.get(level, 'info'))

    filepath = Path(filepath)
    if not filepath.exists(): filepath.touch()
    file_handler = logging.FileHandler(filepath)
    fmt = '\n' + '='*width + '\n%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if stdout:
        std_handler = logging.StreamHandler(sys.stdout)
        std_handler.setLevel(logging.DEBUG)
        std_handler.setFormatter(formatter)
        logger.addHandler(std_handler)
    for hdl in extra_handlers:
        logger.addHandler(hdl)
    return logger

###############################################################################
## CLASSES
###############################################################################
class Udeclogger(object):

    '''
    A decorator for variant use
    '''

    def __init__(self, ltype='excexe', logger=None, *args, **kwargs):
        self.ltype = ltype
        self.logger = logger
        self.args = args
        self.kwargs = kwargs

        self.mode = 'decorating'
    
    def __call__(self, *args, **kwargs):
        if self.mode == 'decorating':
            if self.ltype == 'execution':
                self.func = self.execution_logger(args[0], *self.args, **self.kwargs)
            elif self.ltype == 'exception':
                self.func = self.exception_logger(args[0], *self.args, **self.kwargs)
            elif self.ltype == 'excexe':
                self.func = self.excexe_logger(args[0], *self.args, **self.kwargs)
            self.mode = 'calling'
            return self
        
        self.suppress = kwargs.pop('suppress', False)
        self.prefix = kwargs.pop('prefix', '')
        self.suffix = kwargs.pop('suffix', '')

        if len(args) > 0:
            # print(args)
            if hasattr(args[0], 'logger'):
                self.logger = args[0].logger
        elif self.logger is None:
            self.logger = create_logger()
        r = self.func(*args, **kwargs)
        return r

    def __get__(self, instance, cls):
        return partial(self.__call__, instance)

    def execution_logger(self, func):
        @wraps(func)
        def decorator(*args, **kwargs):
            self.suppress or self.logger.info('{}Executing {}() {}...{}'.format(self.prefix, func.__name__, '' if func.__doc__ is None else func.__doc__, self.suffix))
            r = func(*args, **kwargs)
            self.suppress or self.logger.info('{}Execution of {}() ended{}'.format(self.prefix, func.__name__, self.suffix))
            return r
        return decorator
    
    def exception_logger(self, func, re_raise=True):
        @wraps(func)
        def decorator(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.suppress or self.logger.exception('{}An exeception "{}" occurred when executing {}(){}.'.format(self.prefix, e.__class__.__name__, func.__name__, self.suffix))
                if re_raise:
                    raise
                return False
        return decorator
    
    def excexe_logger(self, func, re_raise=True):
        @wraps(func)
        def decorator(*args, **kwargs):
            self.suppress or self.logger.info('{}Executing {}() {}...{}'.format(self.prefix, func.__name__, '' if func.__doc__ is None else func.__doc__, self.suffix))
            try:
                r = func(*args, **kwargs)
            except Exception as e:
                self.suppress or self.logger.exception('{}An exeception "{}" occurred when executing {}(){}.'.format(self.prefix, e.__class__.__name__, func.__name__, self.suffix))
                if re_raise:
                    raise
                else:
                    return False
            else:
                self.suppress or self.logger.info('{}Execution of {}() ended{}'.format(self.prefix, func.__name__, self.suffix))
                return r
        return decorator