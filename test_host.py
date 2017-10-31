from unittest.mock import patch, call
from tornado.testing import AsyncHTTPTestCase
from http import HTTPStatus
import json
import redis

import main


class HostHandlerTest(AsyncHTTPTestCase):
    __PARAM_HOST = {'name': 'newifi', 'datetime': '12345'}
    __redis = {}

    @staticmethod
    def __redis_keys(pattern='*'):
        return HostHandlerTest.__redis.keys()

    @staticmethod
    def __redis_hset(key, field, value):
        if key in HostHandlerTest.__redis:
            HostHandlerTest.__redis[key][field] = value
        else:
            HostHandlerTest.__redis[key] = {field: value}
        return True

    @staticmethod
    def __redis_hget(key, field):
        return HostHandlerTest.__redis[key][field]

    @staticmethod
    def __redis_hkeys(key):
        return HostHandlerTest.__redis[key].keys()

    @staticmethod
    def __redis_delete(keys):
        for key in keys:
            HostHandlerTest.__redis.pop(key, None)
        return True

    def get_app(self):
        return main.make_app({'host': 'localhost', 'port': 6379})

    def test_post_host(self):
        HostHandlerTest.__redis.clear()
        with patch.object(redis.StrictRedis, 'keys', side_effect=HostHandlerTest.__redis_keys):
            with patch.object(redis.StrictRedis, 'hset', side_effect=HostHandlerTest.__redis_hset) as mock_set:
                mock_set.return_value = 1
                response = self.fetch('/host', method="POST", body=json.dumps(HostHandlerTest.__PARAM_HOST))
                fields = list(HostHandlerTest.__PARAM_HOST.keys())
                self.assertEqual(mock_set.mock_calls,
                                 [call(HostHandlerTest.__PARAM_HOST[fields[0]], fields[0], HostHandlerTest.__PARAM_HOST[fields[0]]),
                                  call(HostHandlerTest.__PARAM_HOST[fields[0]], fields[1], HostHandlerTest.__PARAM_HOST[fields[1]])])
                self.assertEqual(HostHandlerTest.__redis_hget(HostHandlerTest.__PARAM_HOST[fields[0]], fields[0]), HostHandlerTest.__PARAM_HOST[fields[0]])
                self.assertEqual(HostHandlerTest.__redis_hget(HostHandlerTest.__PARAM_HOST[fields[0]], fields[1]), HostHandlerTest.__PARAM_HOST[fields[1]])
                self.assertEqual(response.code, HTTPStatus.CREATED.value)

    def test_get_test(self):
        hostname = HostHandlerTest.__PARAM_HOST['name'].encode()
        HostHandlerTest.__redis[hostname] = {b'name': b'newifi', b'datetime': b'12345'}
        with patch.object(redis.StrictRedis, 'hkeys', side_effect=HostHandlerTest.__redis_hkeys) as mock_hkeys:
            with patch.object(redis.StrictRedis, 'hget', side_effect=HostHandlerTest.__redis_hget) as mock_hget:
                response = self.fetch('/host/newifi', method="GET")
                self.assertEqual(mock_hget.mock_calls,
                                 [call(HostHandlerTest.__PARAM_HOST['name'].encode(), b'name'),
                                  call(HostHandlerTest.__PARAM_HOST['name'].encode(), b'datetime')])
                self.assertEqual(response.code, HTTPStatus.OK.value)
                self.assertEqual(response.body, json.dumps({'hosts': [HostHandlerTest.__PARAM_HOST]}).encode())

    def test_get_all_host(self):
        hostname = HostHandlerTest.__PARAM_HOST['name'].encode()
        HostHandlerTest.__redis[hostname] = {b'name': b'newifi', b'datetime': b'12345'}
        with patch.object(redis.StrictRedis, 'keys', side_effect=HostHandlerTest.__redis_keys) as mock_keys:
            with patch.object(redis.StrictRedis, 'hkeys', side_effect=HostHandlerTest.__redis_hkeys) as mock_hkeys:
                with patch.object(redis.StrictRedis, 'hget', side_effect=HostHandlerTest.__redis_hget) as mock_hget:
                    response = self.fetch('/host', method="GET")
                    mock_keys.assert_called()
                    self.assertEqual(mock_hget.mock_calls,
                                     [call(HostHandlerTest.__PARAM_HOST['name'].encode(), b'name'),
                                      call(HostHandlerTest.__PARAM_HOST['name'].encode(), b'datetime')])
                    self.assertEqual(response.code, HTTPStatus.OK.value)
                    self.assertEqual(response.body, json.dumps({'hosts': [HostHandlerTest.__PARAM_HOST]}).encode())

    def test_delete_host(self):
        hostname = HostHandlerTest.__PARAM_HOST['name']
        HostHandlerTest.__redis[hostname] = HostHandlerTest.__PARAM_HOST
        with patch.object(redis.StrictRedis, 'delete', side_effect=HostHandlerTest.__redis_delete) as mock_delete:
            mock_delete.return_value = 1
            response = self.fetch('/host/newifi', method="DELETE")
            self.assertEqual(response.code, HTTPStatus.OK.value)
            self.assertEqual(len(HostHandlerTest.__redis_keys()), 0)
