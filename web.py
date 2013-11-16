#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

import tornado.httpserver
import tornado.ioloop
import tornado.autoreload
import tornado.options
import tornado.web
import tornado.gen
from tornado import httpclient
import os

from tornado.options import define, options
define("port", default=int(os.getenv('PORT', 5000)), help="run on the given port", type=int)

class Child:
    def __init__(self, rq, num, children=[]):
        self.rq = rq
        self.num = num
        self.children = children

    @tornado.gen.coroutine
    def run(self):
        # print "+ T", self.rq, "C", self.num
        if isinstance(self, AsyncChild):
            yield self()
        else:
            self()
        # print "- T", self.rq, "C", self.num
        if self.children:
            yield map(lambda c: tornado.gen.Task(c.run), self.children)

class AsyncChild(Child):
    @tornado.gen.coroutine
    def __call__(self):
        client = httpclient.AsyncHTTPClient()
        yield tornado.gen.Task(client.fetch, "http://google.com")

class SyncChild(Child):
    def __call__(self):
        100 * 100


class MainHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def task_run(self):
        logging.info('Task Starts')
        rq = self.get_argument('rq', '?')
        if self.get_argument('size', None) == 'large':
            self.children = [AsyncChild(rq, 1, [AsyncChild(rq, 2),
                                            AsyncChild(rq, 3, [SyncChild(rq, 4),
                                                           AsyncChild(rq, 5),
                                                           SyncChild(rq, 6)]),
                                            SyncChild(rq, 7)]),
                             SyncChild(rq, 8, [AsyncChild(rq, 9, [AsyncChild(rq, 10),
                                                          AsyncChild(rq, 11, [SyncChild(rq, 12),
                                                                         AsyncChild(rq, 13),
                                                                         SyncChild(rq, 14)]),
                                                          SyncChild(rq, 15)]),
                                           SyncChild(rq, 16)])]
        elif self.get_argument('size', None) == 'medium':
            self.children = [AsyncChild(rq, 1, [AsyncChild(rq, 2),
                                                AsyncChild(rq, 3, [SyncChild(rq, 4),
                                                                   AsyncChild(rq, 5),
                                                                   SyncChild(rq, 6)]),
                                                SyncChild(rq, 7)])]
        else:
            self.children = [SyncChild(rq, 8, [AsyncChild(rq, 9, [SyncChild(rq, 10)])])]


        yield map(lambda c: tornado.gen.Task(c.run), self.children)
        logging.info('Task Ends')

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        # logging.info('Request Begin ' + self.get_argument('rq', ''))
        # self.write('Please wait as I work magic!')
        # self.flush()
        yield tornado.gen.Task(self.task_run)
        # logging.info('Request finished ' + self.get_argument('rq', ''))
        self.render("./example.html")

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[(r"/", MainHandler)], debug=os.getenv('DEBUG'))
    # http_server = tornado.httpserver.HTTPServer(app)
    app.listen(options.port)
    try: 
        ioloop = tornado.ioloop.IOLoop.instance()
        ioloop.start()
    except KeyboardInterrupt:
        ioloop.stop()
