import logging
import json
from http.server import HTTPStatus

import tornado.web
from tornado.web import asynchronous
from tornado.gen import coroutine, Task

from fastjsonschema import compile, JsonSchemaException
import redis


HOST_SCHEMA = {
    '$schema': 'https://json-schema.org/draft-04/schema#',
    'title': 'Host',
    'oneOf': [
        {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'datetime': {'type': 'string'}
            },
            'required': ['name', 'datetime'],
            'additionalProperties': False
        },
        {
            'type': 'object',
            'properties': {
                'name': {'type': 'array', 'items': {'type': 'string'}}
            },
            'required': ['name'],
            'additionalProperties': False
        }
    ]

}


class HostHandler(tornado.web.RequestHandler):
    LOGGER = logging.getLogger(__name__)

    def __init__(self, application, request, **kwargs):
        self.__redis = None  # type: redis.StrictRedis
        self.__request_body_validator = compile(HOST_SCHEMA)
        super().__init__(application, request, **kwargs)

    def initialize(self, redis_db: dict):
        self.__redis = redis.StrictRedis(redis_db['redis-host'], redis_db['redis-port'])

    @asynchronous
    @coroutine
    def post(self, *args, **kwargs):
        try:
            request_body = json.loads(self.request.body.decode())  # type: dict
            self.__request_body_validator(request_body)
            status = yield Task(self.__put_hosts, request_body)
            self.set_status(status)
            self.finish()
        except JsonSchemaException as e:
            HostHandler.LOGGER.error("Invalid request body: %s", e.message)
            raise e

    @coroutine
    def __put_hosts(self, request_body: dict) -> int:
        hostname = request_body['name']
        status = HTTPStatus.CREATED.value
        if len(self.__redis.keys(hostname)) != 0:
            status = HTTPStatus.OK.value

        for field in request_body:
            self.__redis.hset(hostname, field, request_body[field])
        return status

    @asynchronous
    @coroutine
    def get(self, *args, **kwargs):
        hosts = yield Task(self.__get_hosts, args)
        self.finish({'hosts': hosts})

    @coroutine
    def __get_hosts(self, args):
        hosts = []
        if len(args) == 0:
            host_names = self.__redis.keys()
            for host in host_names:
                hosts.append(self.__get_host_item(host))
        else:
            host_name = args[0]
            hosts.append(self.__get_host_item(host_name))
        return hosts

    def __get_host_item(self, host_name):
        if isinstance(host_name, str):
            host_name = host_name.encode()
        elif not isinstance(host_name, bytes):
            raise TypeError
        item = {}
        for field in self.__redis.hkeys(host_name):
            item[field.decode()] = self.__redis.hget(host_name, field).decode()

        return item

    @asynchronous
    @coroutine
    def delete(self, *args, **kwargs):
        yield Task(self.__remove_hosts, args)
        self.finish()

    @coroutine
    def __remove_hosts(self, args):
        for arg in args:
            self.__redis.delete(arg)
        return None
