#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import os
import time
import types
import asyncio


def _check_update(check_time):
    result = None
    for modules in sys.modules.values():
        if not isinstance(modules, types.ModuleType):
            continue

        f_path = getattr(modules, '__file__', None)
        if not f_path:
            continue

        if f_path.endswith(".pyc") or f_path.endswith(".pyo"):
            f_path = f_path[:-1]
            
        try:
            m_time = os.stat(f_path).st_mtime
        except OSError as e:
            continue

        if m_time > check_time:
            return f_path

@asyncio.coroutine
def autoreload():
    while 1:
        check_time = time.time()
        yield from asyncio.sleep(2)
        f_path = _check_update(check_time)
        if f_path:
            logging.info('restarting server: {} modified'.format(f_path))
            os.execv(sys.executable, [sys.executable] + sys.argv)

