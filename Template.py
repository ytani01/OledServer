#!/usr/bin/env python3
#
# (C) 2018 Yoichi Tanibayashi
#
import telnetlib
import time
import click

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
#handler_fmt = Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
handler_fmt = Formatter('%(asctime)s %(levelname)s %(funcName)s> %(message)s',
                        datefmt='%H:%M:%S')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False

#####
class OledClient:
    DEF_HOST = 'localhost'
    DEF_PORT = 12345

    def __init__(self, server='', port=0):
        pass
    
#####
@click.command(help='OLED client')
@click.argument('server', type=str, default='')
@click.argument('port', type=int, default=0)
def main(server, port):
    cl = OledClient(server, port)

if __name__ == '__main__':
    main()
