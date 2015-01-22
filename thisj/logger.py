#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging.handlers

def init_logger(loglevel='error', logfile=None, debug=False):
    _map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warn': logging.WARN,
        'error': logging.ERROR,
    }
    loglevel = _map.get(loglevel, logging.ERROR)
    
    logger = logging.getLogger()
    formatter = _LogFormatter(color=debug)
    
    if debug or not logfile:
        handler = logging.StreamHandler()
    else:
        handler = logging.handlers.TimedRotatingFileHandler(logfile, when='midnight')
        
    handler.setFormatter(formatter)
    handler.setLevel(loglevel)
    logger.setLevel(loglevel)
    logger.addHandler(handler)

class _LogFormatter(logging.Formatter):
    u"""Custom log format"""
    def __init__(self, color, *args, **kwargs):
        super(_LogFormatter, self).__init__(*args, **kwargs)

        self._color = color
        self._colors = {
            logging.DEBUG: '\x1b[34m', # Blue
            logging.INFO: '\x1b[32m', # Green
            logging.WARNING: '\x1b[33m', # Yellow
            logging.ERROR: '\x1b[31m', # Red
        }
        self._normal = '\x1b(B\x1b[m'
        
    def format(self, record):
        record.asctime = self.formatTime(record, '%Y-%m-%d %H:%M:%S')
        
        prefix = '[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d]' % record.__dict__
        if self._color:
            prefix = self._colors.get(record.levelno, self._normal) + prefix + self._normal
        
        if record.exc_info:
            formatted = prefix + '\n' + self.formatException(record.exc_info)
        else:
            formatted = prefix + ' ' + record.getMessage()
            
        return formatted
    
