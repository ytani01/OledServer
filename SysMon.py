#!/usr/bin/env python3
#
# (C) 2018 Yoichi Tanibayashi
#
import sys
import os
import subprocess
import re
import click

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler_fmt = Formatter('%(asctime)s %(levelname)s %(funcName)s> %(message)s',
                        datefmt='%H:%M:%S')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False

#####
class SysMon:
    CMD_PS = ['ps', 'auxww']
    DEF_SERVER = 'localhost'
    DEF_PORT = 12345

    def __init__(self, keyword, server='', port=0):
        self.keyword = keyword
        
        self.server, self.port = __class__.DEF_SERVER, __class__.DEF_PORT
        if server != '':
            self.server = server
        if port != 0:
            self.port = port

        self.myname = sys.argv[0]
        logger.debug('self.myname=%s', self.myname)
        
        self.proc = subprocess.run(__class__.CMD_PS,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        if self.proc.returncode != 0:
            logger.error('stderr=%s', self.proc.stderr)
            return None

        # returncode == 0
        self.stdout = [l.split() for l in self.proc.stdout.splitlines()]
        self.psout = []
        for l in self.stdout:
            if '%CPU' in l[2]:
                continue
            if self.myname in ' '.join(l[10:]):
                continue
            self.psout.append({'cpu':l[2], 'mem':l[3], 'time':l[9],
                               'cmd':' '.join(l[10:])})
        #logger.debug(self.psout)

        if len(keyword) > 0:
            self.find_list = []
            for l in self.psout:
                for k in keyword:
                    if re.search(k, l['cmd']):
                        self.find_list.append(l)
                        break
        else:
            self.find_list = self.psout

    def __enter__(self):
        self.open()

    def __exit__(self, ex_type, ex_value, trace):
        logger.debug('(%s, %s, %s)', ex_type, ex_value, trace)
        self.close()

    def open(self):
        pass

    def close(self):
        pass
    
    def print(self):
        for l in self.find_list:
            print('[%s,%s]: %s' % (l['cpu'], l['mem'], l['cmd']))
    
#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS, help='Template program')
@click.argument('keyword', type=str, nargs=-1)
@click.option('--server', '-s', 'server', type=str, default='localhost',
              help='server\'s hostname or IP address')
@click.option('--port', '-p', 'port', type=int, default=0,
              help='server\'s port number')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(keyword, server, port, debug):
    logger.setLevel(INFO)
    if debug:
        logger.setLevel(DEBUG)

    logger.debug('keyword=\'%s\', server=\'%s\', port=%d',
                 keyword, server, port)
    
    obj = SysMon(list(keyword), server, port)
    obj.print()

if __name__ == '__main__':
    main()
