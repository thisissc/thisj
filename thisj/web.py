#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import mimetypes
import os.path
import re
import sys
import urllib.parse
from aiohttp import abc
from aiohttp import web
from aiohttp import protocol
from jinja2 import Environment
from jinja2 import FileSystemLoader
import thisj


class BaseHandler:
    def __init__(self):
        self._request = None
        self._response = None
        self._args = []
        self._kwargs = {}

    @property
    def request(self):
        return self._request

    @property
    def response(self):
        if self._response is None:
            self._response = web.Response()
            self._response.content_type = 'text/html'
        return self._response

    def render(self, tpl, **data):
        env = _JinjaEnv.instance()
        template = env.get_template(tpl)
        return template.render(**data)

    def redirect(self, location):
        raise web.HTTPFound(location)

    def set_handler_args(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    @asyncio.coroutine
    def __call__(self, request):
        self._request = request

        method = request.method
        handler = getattr(self, method.lower(), None)

        if handler:
            body = handler(*self._args, **self._kwargs)
            if hasattr(body, '__next__'):
                body = yield from body
            self.response.text = body
            return self.response
        else:
            raise web.HTTPMethodNotAllowed(method, []) # TODO: second paramter "allowed_method" is empty


class StaticFileHandler(BaseHandler):
    def __init__(self, staticpath='static/'):
        if staticpath.startswith('/'):
            staticpath = staticpath[1:]
        staticpath = os.path.abspath(staticpath)
        self._staticpath = staticpath
        super(StaticFileHandler, self).__init__()

    def get(self, filename):
        resp = self.response
        path = os.path.join(self._staticpath, filename)

        if os.path.exists(path):
            ct = mimetypes.guess_type(filename)[0]
            ct = ct or 'application/octet-stream'
            resp.content_type = ct
            resp.enable_chunked_encoding(1024)

            resp.start(self.request)
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                while chunk:
                    resp.write(chunk)
                    chunk = f.read(1024)

            return ''
        else:
            raise web.HTTPNotFound()

    @property
    def response(self):
        if self._response is None:
            self._response = web.StreamResponse()
        return self._response


class Application(web.Application):
    def __init__(self, tplpath='templates', handlers=None):
        protocol.HttpMessage.SERVER_SOFTWARE = 'thisj/{1}'.format(sys.version_info, thisj.__version__)
        router = _SimpleRouter()
        router.add_handlers(handlers)
        _JinjaEnv.init(tplpath)

        super(Application, self).__init__(router=router)


class _SimpleMatchInfo(abc.AbstractMatchInfo):
    def __init__(self, handler):
        self._handler = handler

    @property
    def handler(self):
        return self._handler


class _SimpleRouter(abc.AbstractRouter):
    def __init__(self):
        super(_SimpleRouter, self).__init__()
        self._handlers = []

    def add_handlers(self, handlers):
        for item in handlers:
            self.add_handler(*item)

    def add_handler(self, pattern, handler, *args, **kwargs):
        if not pattern.endswith('$'):
            pattern += '$'
        prog = re.compile(pattern)
        self._handlers.append((prog, handler, args, kwargs))

    @asyncio.coroutine
    def resolve(self, request):
        path = request.path
        method = request.method

        for prog, handler_class, args, kwargs in self._handlers:
            match = prog.match(path)
            if match:
                handler = handler_class(*args, **kwargs)
                handler_args = [urllib.parse.unquote(x) for x in match.groups()]
                handler.set_handler_args(*handler_args)
                match_info = _SimpleMatchInfo(handler)
                return match_info

        raise web.HTTPNotFound()


class _JinjaEnv:
    _env_obj = None

    @staticmethod
    def init(tplpath):
        _JinjaEnv._env_obj = Environment(loader=FileSystemLoader(tplpath))

    @staticmethod
    def instance():
        return _JinjaEnv._env_obj

