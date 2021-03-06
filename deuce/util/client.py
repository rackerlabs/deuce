import aiohttp
import asyncio
import hashlib
import json
from swiftclient.exceptions import ClientException

from deuce import conf
from deuce.util.event_loop import get_event_loop

# NOTE (TheSriram) : must include exception handling


def _noloop_request(method, url, headers, data=None):
    response = yield from aiohttp.request(method=method, url=url,
                                          headers=headers, data=data)
    return response


@get_event_loop
def _async_request(method, url, headers, names, contents, etag):
    tasks = []
    for name, content in zip(names, contents):
        # NOTE(THeSriram) : xyu discovered that we received 422's
        # from swift if we didn't execute a copy of headers
        # containing the msd5 of block data
        headers = headers.copy()
        if etag:
            mdhash = hashlib.md5()
            mdhash.update(content)
            mdetag = mdhash.hexdigest()
            headers.update(
                {'Etag': mdetag, 'Content-Length': str(len(content))})
        else:
            headers.update({'Content-Length': str(len(content))})
        tasks.append(
            asyncio.Task(
                _noloop_request(
                    'PUT',
                    url +
                    str(name),
                    headers=headers,
                    data=content)))
    total_responses = yield from asyncio.gather(*tasks)
    return total_responses


@get_event_loop
def _request(method, url, headers, data=None):
    response = yield from aiohttp.request(method=method, url=url,
                                          headers=headers, data=data)
    return response


@get_event_loop
def _request_getobj(method, url, headers, data=None):
    response = yield from aiohttp.request(method=method, url=url,
                                          headers=headers, data=data)

    block = yield from response.content.read()
    return (response, block)


@get_event_loop
def _request_getcontainer(method, url, headers, data=None):
    response = yield from aiohttp.request(method=method, url=url,
                                          headers=headers, data=data)

    content = yield from response.content.read()
    return (response, content)


# Create vault
def put_container(url, token, container, response_dict):
    headers = {'X-Auth-Token': token}
    response = _request('PUT', url + '/' + container, headers=headers)
    response_dict['status'] = response.status


# Check Vault
def head_container(url, token, container):
    headers = {'X-Auth-Token': token}
    response = _request('HEAD', url + '/' + container, headers=headers)

    if response.status >= 200 and response.status < 300:
        return response.headers
    else:
        raise ClientException("Vault HEAD failed")


def get_container(url, token, container, limit=None, marker=None):

    if not limit:
        limit = conf.api_configuration.default_returned_num
    qs = '?limit={0}'.format(limit)

    if marker:
        qs = qs + '&marker={0}'.format(marker)

    req_url = url + '/' + container + qs

    headers = {'X-Auth-Token': token,
               'Accept': 'application/json'}
    response, content = _request_getcontainer('GET', req_url,
                                              headers=headers)

    if response.status >= 200 and response.status < 300:
        json_content = json.loads(content.decode())
        block_list = [block['name'] for block in json_content]
        return block_list
    else:
        raise ClientException("Vault GET failed")


# Delete Vault
def delete_container(url, token, container, response_dict):
    headers = {'X-Auth-Token': token}
    response = _request('DELETE', url + '/' + container, headers=headers)
    response_dict['status'] = response.status


# Store Block

def put_object(url, token, container, name, contents,
               content_length, etag, response_dict):
    headers = {'X-Auth-Token': token}
    if etag:
        headers.update({'Etag': etag, 'Content-Length': content_length})
    else:
        headers.update({'Content-Length': content_length})
    response = _request('PUT', url + '/' + container + '/' + str(name),
                        headers=headers, data=contents)

    response_dict['status'] = response.status
    return response.headers['etag']


def put_async_object(
        url, token, container, names, contents, etag, response_dict):
    headers = {'X-Auth-Token': token}

    responses = _async_request(
        'PUT',
        url +
        '/' +
        container +
        '/',
        headers,
        names,
        contents,
        etag)

    if all([response.status == 201 for response in responses]):
        response_dict['status'] = 201
    else:
        response_dict['status'] = 500


# Check Block


def head_object(url, token, container, name):
    headers = {'X-Auth-Token': token}
    response = _request(
        'HEAD',
        url +
        '/' +
        container +
        '/' +
        str(name),
        headers=headers)

    if response.status >= 200 and response.status < 300:
        return response.headers
    else:
        raise ClientException("Block HEAD failed")


# Delete Block
def delete_object(url, token, container, name, response_dict):
    headers = {'X-Auth-Token': token}
    response = _request(
        'DELETE',
        url +
        '/' +
        container +
        '/' +
        str(name),
        headers=headers)

    response_dict['status'] = response.status


# Get Block

def get_object(url, token, container, name, response_dict):
    headers = {'X-Auth-Token': token}
    (response, block) = _request_getobj(
        'GET',
        url +
        '/' +
        container +
        '/' +
        str(name),
        headers=headers)

    response_dict['status'] = response.status

    return (response, block)
