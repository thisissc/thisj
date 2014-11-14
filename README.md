# thisj
It's a Python web framework, base on aiohttp which is http client/server for asyncio, and with Jinja2 template engine

### Requirements
See requirements.txt

### Example

``` python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from thisj import server
from thisj import web

class HelloHandler(web.BaseHandler):
    def get(self):
        # template file: ./templates/hello.html
        return self.render('hello.html', name='WORLD')

urls = [
    ('GET', '/', HelloHandler),
]

def main():
    app = web.Application(tplpath='templates', handlers=urls)
    server.serve(app)

if __name__ == '__main__':
   main()
```

templates/hello.html
``` html
Hello {{ name }}!
```

