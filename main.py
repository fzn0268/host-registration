#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging.config

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options

import host


PROJECT_NAME = 'host-registration'


define('port', 8888, int, 'Port that server listens on')
define('address', '127.0.0.1', str, 'Address that server binds')
define('redis-port', 6379, int, 'Port of redis listening', group='redis_db')
define('redis-host', 'localhost', str, 'Host of redis', group='redis_db')
define('debug', False, bool, 'Run handlers in debug mode')


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


def make_app(redis_db: dict):
    settings = {'debug', options.debug}

    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/host", host.HostHandler, dict(redis_db=redis_db)),
        (r"/host/(.*)", host.HostHandler, dict(redis_db=redis_db))
    ], settings)


if __name__ == "__main__":
    logging.config.fileConfig('logging.conf')
    logger = logging.getLogger(PROJECT_NAME)
    logger.setLevel(logging.INFO)

    '''  
    Get the option(s) from the startup command line if ever.  

    In this tutorial, we define own "port" option to change the  
    port via the command line, and then we can run multiple tornado  
    processes at different ports.  
    '''
    options.parse_command_line()

    # Below lines should be after the parse_command_line()
    app = make_app(options.group_dict('redis_db'))

    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)

    http_server.listen(options.port, options.address)

    tornado.ioloop.IOLoop.instance().start()
