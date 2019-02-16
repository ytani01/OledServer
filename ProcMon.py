#!/usr/bin/env python3
#
# (C) 2018 Yoichi Tanibayashi
#
import sys
import os
import subprocess
import re
import time
from OledClient import OledClient
import click

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
logger.setLevel(INFO)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler_fmt = Formatter('%(asctime)s %(levelname)s %(name)s %(funcName)s> %(message)s',
                        datefmt='%H:%M:%S')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False

#####
class ProcMon:
    CMD_PS          = ['ps', 'auxww']
    DEF_OLED_SERVER = 'localhost'
    DEF_OLED_PORT   = 12345

    def __init__(self, keyword, oled_part='', oled_server='', oled_port=0):
        self.keyword     = keyword
        self.oled_part   = oled_part
        self.oled_server = oled_server
        self.oled_port   = oled_port

        if self.oled_part != '':
            self.oled_part = 'body'
            if self.oled_part[0] == 'h':
                self.oled_part = 'header'
            if self.oled_part[0] == 'f':
                self.oled_part = 'footer'
            
        if self.oled_server != '':
            self.oled_server	= __class__.DEF_OLED_SERVER
        if self.oled_port != 0:
            self.oled_port	= __class__.DEF_OLED_PORT

        self.myname	= sys.argv[0]
        self.pid	= os.getpid()
        logger.debug('self.myname=%s, pid=%d', self.myname, self.pid)
        
        self.proc	= subprocess.Popen(__class__.CMD_PS,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           universal_newlines=True)
        self.cmd_pid	= self.proc.pid
        [out, err]	= self.proc.communicate()
        if self.proc.returncode != 0:
            logger.error('stderr=%s', err)
            return None

        # returncode == 0
        self.stdout = [l.split() for l in out.splitlines()]
        #logger.debug('self.stdout=%s', self.stdout)
        self.stdout.pop(0)	# ignore first line
        self.psout = []
        for l in self.stdout:
            pid	= int(l[1])
            cpu	= float(l[2])
            mem	= float(l[3])
            tm	= l[9]
            cmd	= ' '.join(l[10:])
            if pid == self.pid or pid == self.cmd_pid:
                logger.debug('ignore: %d %s', pid, cmd)
                continue
            self.psout.append({'pid':pid, 'cpu':cpu, 'mem':mem, 'time':tm,
                               'cmd':cmd})
        #logger.debug('psout=%s', self.psout)

        self.find_list = {}
        if len(self.keyword) > 0:
            for k in self.keyword:
                self.find_list[k] = []
            for l in self.psout:
                for k in self.keyword:
                    [key_str, disp_str] = [k, k]
                    if ':' in k:
                        key_str, disp_str = k.split(':')
                        
                    if re.search(key_str, l['cmd']):
                        self.find_list[k].append(l)
                        break
        else:
            self.find_list[''] = list(self.psout)
        logger.debug('find_list=%s', self.find_list)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, ex_type, ex_value, trace):
        logger.debug('(%s, %s, %s)', ex_type, ex_value, trace)
        self.close()

    def open(self):
        pass

    def close(self):
        pass
    
    def print_list(self):
        for k in self.find_list.keys():
            [key_str, disp_str] = [k, k]
            if ':' in k:
                key_str, disp_str = k.split(':')
            for l in self.find_list[k]:
                print('\'%s\' [%5d,%.2f,%.2f]: %s' % (disp_key, l['pid'],
                                                  l['cpu'], l['mem'],
                                                  l['cmd']))

    def get_statline(self, sym=False):
        out_line = []
        for k in self.keyword:
            n = len(self.find_list[k])
            [key_str, disp_str] = [k, k]
            if ':' in k:
                key_str, disp_str = k.split(':')

            if sym:
                if n > 0:
                    s = '*'
                else:
                    s = ' '
            else:
                if n >= 10 :
                    s = '+'
                else:
                    s = str(n)
            out_line.append('%s:%s' % (s, disp_str))
        return out_line
    
    def print_statline(self, sym=False):
        for l in self.get_statline(sym):
            print(l)

    def oled_statline(self, sym=False):
        if self.oled_part == '':
            return
        
        with OledClient(self.oled_server, self.oled_port) as ol:
            ol.part(self.oled_part)
            ol.row(0)
            ol.crlf(True)
            ol.zenkaku(True)
            ol.clear()
            for l in self.get_statline(sym):
                ol.send(l)

    def get_statstr(self, sym=False):
        out_str = '['
        for k in self.keyword:
            n = len(self.find_list[k])
            if sym:
                if n > 0:
                    out_str += '*'
                else:
                    out_str += ' '
            else:
                if n >= 10:
                    out_str += '+'
                else:
                    out_str += str(n)
        out_str += ']'
        return out_str
    
#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('keyword', metavar='[keyword]...', type=str, nargs=-1)
@click.option('--interval', '-i', 'interval', type=int, default=1,
              help='interval sec')
@click.option('--count', '-c', 'count', type=int, default=0,
              help='count')
@click.option('--oled-part', '--oled', '-o', 'oled_part', type=str, default='',
              help='OLED switch: body/header/footer')
@click.option('--oled-server', '-os', 'oled_server', type=str,
              default='localhost',
              help='OLED server\'s hostname or IP address')
@click.option('--oled-port', '-op', 'oled_port', type=int, default=0,
              help='OLED server\'s port number')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(keyword, interval, count, oled_part, oled_server, oled_port, debug):
    '''
Process Monitor

Arguments:

    [keyword]
    '<regular expression>[:disp_str]'
    '''
    
    global logger

    logger.setLevel(INFO)
    if debug:
        logger.setLevel(DEBUG)

    logger.debug('keyword=\'%s\', oled_part=%s, oled_server=\'%s\', oled_port=%d',
                 keyword, oled_part, oled_server, oled_port)
    
    prev_statstr = ''

    i = 0
    while True:
        with ProcMon(list(keyword), oled_part, oled_server, oled_port) as pm:
            statstr = pm.get_statstr(True)
            logger.debug('statstr=%s, prev_statstr=%s', statstr, prev_statstr)
            if statstr != prev_statstr:
                pm.oled_statline(True)
                prev_statstr = statstr
            
        i += 1
        if count != 0 and i >= count:
            break

        time.sleep(interval)

if __name__ == '__main__':
    main()
