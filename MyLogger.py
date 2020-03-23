#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
"""
MyLogger.py

Usage:

--
from MyLogger import get_logger

class A:
    def __init__(self, a, debug=False)
        self.debug = debug
        self.logger = get_logger(__class__.__name__, self.debug)
        self.logger.debug('a=%s', a)
--

"""
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN


class MyLogger:
    def __init__(self, name=''):
        fmt_hdr = '%(asctime)s %(levelname)s '
        fmt_loc = '%(filename)s.%(name)s.%(funcName)s:%(lineno)d> '
        self.handler_fmt = Formatter(fmt_hdr + fmt_loc + '%(message)s',
                                     datefmt='%H:%M:%S')

        self.console_handler = StreamHandler()
        self.console_handler.setLevel(DEBUG)
        self.console_handler.setFormatter(self.handler_fmt)

        self.logger = getLogger(name)
        self.logger.setLevel(INFO)
        self.logger.addHandler(self.console_handler)
        self.logger.propagate = False

    def get_logger(self, name, debug):
        logger = self.logger.getChild(name)
        if debug:
            logger.setLevel(DEBUG)
        else:
            logger.setLevel(INFO)
        return logger


myLogger = MyLogger()


def get_logger(name, debug):
    return myLogger.get_logger(name, debug)
