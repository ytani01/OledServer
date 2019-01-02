#!/usr/bin/env python3
#
# (C) 2018 Yoichi Tanibayashi
#
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
class MainClass:
    DEF_SERVER = 'localhost'
    DEF_PORT = 12345

    def __init__(self, server='', port=0):
        self.server, self.port = __class__.DEF_SERVER, __class__.DEF_PORT
        if server != '':
            self.server = server
        if port != 0:
            self.port = port

    def func1(self, text):
        logger.debug('text=\'%s\'', text)
        
        logger.info('%s:%d', self.server, self.port)
        print(text)
        
    
#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS, help='Template program')
@click.argument('text', type=str, default='Hello world !')
@click.option('--server', '-s', 'server', type=str, default='localhost',
              help='server\'s hostname or IP address')
@click.option('--port', '-p', 'port', type=int, default=0,
              help='server\'s port number')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(text, server, port, debug):
    logger.setLevel(INFO)
    if debug:
        logger.setLevel(DEBUG)

    logger.debug('text=\'%s\', server=\'%s\', port=%d', text, server, port)
    
    obj = MainClass(server, port)
    obj.func1(text)

if __name__ == '__main__':
    main()
