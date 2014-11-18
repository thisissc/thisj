#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
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
    def __init__(self, tplpath='templates', staticprefix='/s', staticpath='static', handlers=None):
        router = _SimpleRouter()
        router.add_handlers(handlers)
        router.add_static(staticprefix, staticpath)
        _JinjaEnv.init(tplpath)

        super(Application, self).__init__(router=router)


class _SimpleRouter(web.UrlDispatcher):
    def add_handler(self, method, pattern, handler):
        self.add_route(method.upper(), pattern, handler)

    def add_handlers(self, handler_list):
        if handler_list:
            for method, pattern, handler in handler_list:
                self.add_handler(method, pattern, handler)

    @asyncio.coroutine
    def resolve(self, request):
        match_info = yield from super(_SimpleRouter, self).resolve(request)
        if not request.path.startswith('/s/'): # FIXME: start with /s/, shoud be a var str
            handler = match_info.handler
            handler = handler()
            handler = getattr(handler, request.method.lower())
            _entry = match_info._entry
            match_info._entry = web.Entry(_entry.regex, _entry.method, handler, _entry.endpoint, _entry.path, _entry.type)
        return match_info


class _JinjaEnv:
    _env_obj = None

    @staticmethod
    def init(tplpath):
        _JinjaEnv._env_obj = Environment(loader=FileSystemLoader(tplpath))

    @staticmethod
    def instance():
        return _JinjaEnv._env_obj

