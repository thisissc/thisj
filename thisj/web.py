#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
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
        self._deco_method('get')
        self._deco_method('post')

        self._request = None
        self._response = None

    def _deco_method(self, method):
        fn = getattr(self, method, None)
        
        if fn:
            def _tmp_f(*args, **kwargs):
                def _f(request):
                    self._request = request
                    body = fn(*args, **kwargs)
                    if isinstance(body, str):
                        body = body.encode('utf-8')
                    self.response.body = body
                    return self.response

                _f = asyncio.coroutine(_f)
                return _f
            setattr(self, method, _tmp_f)

    @property
    def request(self):
        return self._request

    @property
    def response(self):
        if self._response is None:
            self._response = web.Response(self._request)
        return self._response

    def render(self, tpl, **data):
        env = _JinjaEnv.instance()
        template = env.get_template(tpl)
        return template.render(**data)


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

        ct = mimetypes.guess_type(filename)[0]
        ct = ct or 'application/octet-stream'
        resp.content_type = ct
        resp.headers['transfer-encoding'] = 'chunked'
        resp.send_headers()

        with open(path, 'rb') as f:
            chunk = f.read(1024)
            while chunk:
                resp.write(chunk)
                chunk = f.read(1024)

        return ''

    @property
    def response(self):
        if self._response is None:
            self._response = web.StreamResponse(self.request)
        return self._response


class Application(web.Application):
    def __init__(self, tplpath='templates', handlers=None):
        protocol.HttpMessage.SERVER_SOFTWARE = 'Python/{0[0]}.{0[1]} aiohttp/{1}'.format(sys.version_info, thisj.__version__)
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
                handler = getattr(handler, method.lower())

                if handler:
                    args = [urllib.parse.unquote(x) for x in match.groups()]
                    handler = handler(*args)
                    match_info = _SimpleMatchInfo(handler)
                    return match_info
                else:
                    raise web.HTTPMethodNotAllowed(request, method, []) # TODO: allowed_method is empty

        raise web.HTTPNotFound(request)


class _JinjaEnv:
    _env_obj = None

    @staticmethod
    def init(tplpath):
        _JinjaEnv._env_obj = Environment(loader=FileSystemLoader(tplpath))

    @staticmethod
    def instance():
        return _JinjaEnv._env_obj

