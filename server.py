#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import asyncio
from thisj import autoreload
from thisj import web
from thisj import logger


def _init_args():
    parser = argparse.ArgumentParser(description='start server.')
    parser.add_argument('--host', default='localhost', help='host [%(default)s]')
    parser.add_argument('--port', type=int, default=8000, help='port [%(default)s]')
    parser.add_argument('--loglvl', default='error', choices=['debug', 'info', 'warn', 'error'], help='logging level [%(default)s]')
    parser.add_argument('--logfile', help='path to logging file')
    parser.add_argument('--timeout', type=float, default=None, help='timeout(s)')
    parser.add_argument('--debug', action='store_true', help='start debug mode')
    args = parser.parse_args()
    
    return args

def serve(app):
    args = _init_args()
    logger.init_logger(args.loglvl, args.logfile, args.debug)

    loop = asyncio.get_event_loop()
    coro = loop.create_server(app.make_handler, args.host, args.port)

    if args.debug:
        tasks = [
            coro,
            autoreload.autoreload(),
        ]
        coro = asyncio.wait(tasks)

    loop.run_until_complete(coro)
    logging.info('serving on {}:{}'.format(args.host, args.port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("exit")

