#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import asyncio
from aiohttp import abc
from aiohttp import web
from jinja2 import Environment
from jinja2 import FileSystemLoader


class BaseHandler:
    def __init__(self):
        self._deco_method('get')
        self._deco_method('post')

        self._request = None
        self._response = None

    def _deco_method(self, method):
        fn = getattr(self, method, None)
        
        if fn:
            def _f(request, *args, **kwargs):
                self._request = request
                body = fn(*args, **kwargs)
                if isinstance(body, str):
                    body = body.encode('utf-8')
                self.response.body = body
                return self.response

            _f = asyncio.coroutine(_f)
            setattr(self, method, _f)

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


class Application(web.Application):
    def __init__(self, tplpath='templates', handlers=None):
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
        for p, h in handlers:
            self.add_handler(p, h)

    def add_handler(self, pattern, handler):
        if not pattern.endswith('$'):
            pattern += '$'
        prog = re.compile(pattern)
        self._handlers.append((prog, handler))

    @asyncio.coroutine
    def resolve(self, request):
        path = request.path
        method = request.method

        for prog, handler_class in self._handlers:
            match = prog.match(path)
            if match:
                handler = handler_class()
                handler = getattr(handler, method.lower())

                if handler:
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

