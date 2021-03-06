import json
from deuce.util import client as p3k_swiftclient
from deuce.tests.util.mockfile import MockFile
from deuce.tests import V1Base
from swiftclient.exceptions import ClientException
import mock
import asyncio


class Response(object):

    def __init__(self, status, content=None):
        self.status = status
        self.content = content
        self.headers = {'etag': 'mock'}
        if content:
            fut = asyncio.Future(loop=None)
            fut.set_result(content)
            self.content.read = mock.Mock(return_value=fut)

    def decode(self):
        return self.content.decode()


class Content(object):

    def __init__(self, contents):
        self.contents = contents

    def read(self):
        pass

    def decode(self):
        if isinstance(self.contents, bytes):
            return json.dumps(self.contents.decode())
        else:
            return json.dumps(self.contents)

    def __iter__(self):
        return (content for content in self.contents)


class Test_P3k_SwiftClient(V1Base):

    def setUp(self):
        self.storage_url = 'http://mock_storage_url.com'
        self.token = self.create_auth_token()
        self.vault = self.create_vault_id()
        self.block = self.create_block_id()
        self.blocks = ['mock1', 'mock2']
        self.block_contents = [b'mock', b'mock']
        self.response_dict = dict()

    def test_put_container(self):
        res = Response(201)
        fut = asyncio.Future(loop=None)
        fut.set_result(res)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        p3k_swiftclient.put_container(
            self.storage_url,
            self.token,
            self.vault,
            self.response_dict)
        self.assertEqual(self.response_dict['status'], 201)

    def test_head_container(self):
        res = Response(200)
        fut = asyncio.Future(loop=None)
        fut.set_result(res)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        response = p3k_swiftclient.head_container(
            self.storage_url,
            self.token,
            self.vault)
        self.assertEqual(response, res.headers)
        res_exception = Response(404)
        fut = asyncio.Future(loop=None)
        fut.set_result(res_exception)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        self.assertRaises(ClientException,
                          lambda: p3k_swiftclient.head_container(
                              self.storage_url,
                              self.token,
                              self.vault))

    def test_get_container_marker_limit(self):
        # With marker and limit
        content = Content([{'name': 'mocka'},
                           {'name': 'mockb'},
                           {'name': 'mockc'}])
        limit = 3
        marker = 'mocka'
        res = Response(200, content)
        fut = asyncio.Future(loop=None)
        fut.set_result(res)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        response = p3k_swiftclient.get_container(
            self.storage_url,
            self.token,
            self.vault,
            limit,
            marker)
        self.assertEqual(response, [part['name'] for part in content])

    def test_get_container_no_marker_limit(self):
        # With marker and limit as None
        content = Content([{'name': 'mocka'},
                           {'name': 'mockb'},
                           {'name': 'mockc'}])
        limit = None
        marker = None
        res = Response(200, content)
        fut = asyncio.Future(loop=None)
        fut.set_result(res)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        response = p3k_swiftclient.get_container(
            self.storage_url,
            self.token,
            self.vault,
            limit,
            marker)
        self.assertEqual(response, [part['name'] for part in content])

    def test_get_non_existent_container(self):
        content = Content([{'name': 'mock'}])
        res = Response(404, content)
        fut = asyncio.Future(loop=None)
        fut.set_result(res)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        self.assertRaises(ClientException,
                          lambda: p3k_swiftclient.get_container(
                              self.storage_url,
                              self.token,
                              self.vault))

    def test_delete_container(self):
        res = Response(204)
        fut = asyncio.Future(loop=None)
        fut.set_result(res)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        p3k_swiftclient.delete_container(
            self.storage_url,
            self.token,
            self.vault,
            self.response_dict)
        self.assertEqual(self.response_dict['status'], 204)

    def test_put_object(self):
        res = Response(201)
        fut = asyncio.Future(loop=None)
        fut.set_result(res)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        p3k_swiftclient.put_object(
            self.storage_url,
            self.token,
            self.vault,
            self.block,
            'mock',
            '4',
            None,
            self.response_dict)
        self.assertEqual(self.response_dict['status'], 201)
        p3k_swiftclient.put_object(
            self.storage_url,
            self.token,
            self.vault,
            'mock',
            'mock',
            '4',
            'mock',
            self.response_dict)
        self.assertEqual(self.response_dict['status'], 201)

    def test_put_async_object(self):
        res = Response(201)
        fut = asyncio.Future(loop=None)
        fut.set_result(res)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        p3k_swiftclient.put_async_object(
            self.storage_url,
            self.token,
            self.vault,
            self.blocks,
            self.block_contents,
            False,
            self.response_dict)

        self.assertEqual(self.response_dict['status'], 201)
        p3k_swiftclient.put_async_object(
            self.storage_url,
            self.token,
            self.vault,
            self.blocks,
            self.block_contents,
            True,
            self.response_dict)

        self.assertEqual(self.response_dict['status'], 201)
        res = Response(202)
        fut = asyncio.Future(loop=None)
        fut.set_result(res)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        p3k_swiftclient.put_async_object(
            self.storage_url,
            self.token,
            self.vault,
            self.blocks,
            self.block_contents,
            False,
            self.response_dict)

        self.assertEqual(self.response_dict['status'], 500)

    def test_head_object(self):
        res = Response(204)
        fut = asyncio.Future(loop=None)
        fut.set_result(res)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        response = p3k_swiftclient.head_object(
            self.storage_url,
            self.token,
            self.vault,
            'mock')
        self.assertEqual(res.headers, response)
        res_exception = Response(404)
        fut = asyncio.Future(loop=None)
        fut.set_result(res_exception)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut)
        self.assertRaises(ClientException,
                          lambda: p3k_swiftclient.head_object(
                              self.storage_url,
                              self.token,
                              self.vault,
                              'mock'))

    def test_get_object(self):
        mock_file = MockFile(10)
        r = Response(200, mock_file)
        fut1 = asyncio.Future(loop=None)
        fut1.set_result(r)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut1)

        response, block = p3k_swiftclient.get_object(
            self.storage_url,
            self.token,
            self.vault,
            self.block,
            self.response_dict)
        self.assertEqual(r, response)
        self.assertEqual(mock_file, block)

    def test_delete_object(self):
        r = Response(204)
        fut1 = asyncio.Future(loop=None)
        fut1.set_result(r)
        p3k_swiftclient.aiohttp.request = mock.Mock(return_value=fut1)

        p3k_swiftclient.delete_object(
            self.storage_url,
            self.token,
            self.vault,
            self.block,
            self.response_dict)
        self.assertEqual(self.response_dict['status'], 204)
