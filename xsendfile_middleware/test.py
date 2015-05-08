# -*- coding: utf-8 -*-
"""
"""
from __future__ import absolute_import

import io
import itertools
import os
import sys
import unittest

if sys.version_info >= (3, 0):  # pragma: no cover
    unichr = chr
    text_type = str
else:
    text_type = unicode


class Test_xsendfile_middleware(unittest.TestCase):
    def make_filter(self, app):
        from xsendfile_middleware import xsendfile_middleware
        return xsendfile_middleware(app)

    def test_x_accel_redirect(self):
        def file_app(environ, start_response):
            file = DummyFile(name='/path/fn')
            start_response('200 Okay', [])
            return environ['wsgi.file_wrapper'](file, 4096)
        filtered_app = self.make_filter(file_app)
        environ = { 'X_REDIRECT_MAP': '/path/=/mapped/' }
        status, headers, app_iter = get_response(filtered_app, environ)

        redirect_uris = [value for name, value in headers
                         if name.lower() == 'x-accel-redirect']
        self.assertEqual(redirect_uris, ['/mapped/fn'])

        content_length = [value for name, value in headers
                         if name.lower() == 'content-length']
        self.assertEqual(content_length, [])

    def test_headers_are_strs(self):
        def file_app(environ, start_response):
            file = DummyFile(name='/path/fn')
            start_response('200 Okay', [])
            return environ['wsgi.file_wrapper'](file, 4096)
        filtered_app = self.make_filter(file_app)
        environ = {'X_REDIRECT_MAP': '/path/=/mapped/'}
        status, headers, app_iter = get_response(filtered_app, environ)
        for name, value in headers:
            self.assertTrue(isinstance(value, str))
            self.assertTrue(isinstance(name, str))

    def test_uses_upstream_file_wrapper_if_can_not_redirect(self):
        def file_app(environ, start_response):
            file = DummyFile(name='/path/fn')
            start_response('200 Okay', [])
            return environ['wsgi.file_wrapper'](file, 4096)
        filtered_app = self.make_filter(file_app)
        environ = {
            'wsgi.file_wrapper': DummyFileWrapper,
            'X_REDIRECT_MAP': '/does/not/match/',
            }
        status, headers, app_iter = get_response(filtered_app, environ)
        self.assertEqual(type(app_iter), DummyFileWrapper)
        self.assertEqual(app_iter.file.name, '/path/fn')

    def test_no_redirect_map(self):
        def app(environ, start_response):
            start_response('200 Okay', [])
            return iter(['body'])
        filtered_app = self.make_filter(app)
        status, headers, app_iter = get_response(filtered_app, {})
        self.assertEqual(status, '200 Okay')

    def test_non_ascii_redirect_map(self):
        def app(environ, start_response):
            start_response('200 Okay', [])
            return iter(['body'])
        filtered_app = self.make_filter(app)
        environ = {'X_REDIRECT_MAP': '/path/=/mapped/' + unichr(0xf8)}
        status, headers, app_iter = get_response(filtered_app, environ)
        self.assertEqual(status, '200 Okay')

    def test_passes_on_calls_to_write(self):
        def writer_app(environ, start_response):
            write = start_response('200 Okay', [])
            write('body')
            return iter([])
        filtered_app = self.make_filter(writer_app)
        environ = {'X_REDIRECT_MAP': '/'}
        status, headers, app_iter = get_response(filtered_app, environ)
        self.assertEqual(list(app_iter), ['body'])

    def test_start_response_called_with_exc_info(self):
        def exc_app(environ, start_response):
            try:
                raise DummyException()
            except Exception:
                start_response("200 Okay", [], sys.exc_info())
            return iter([])     # pragma: no cover
        filtered_app = self.make_filter(exc_app)
        environ = {'X_REDIRECT_MAP': '/'}
        self.assertRaises(DummyException, get_response, filtered_app, environ)

    def test_start_response_never_called(self):
        def broken_app(environ, start_response):
            return iter([])
        filtered_app = self.make_filter(broken_app)
        environ = {'X_REDIRECT_MAP': '/'}
        self.assertRaises(StartResponseNeverCalled,
                          get_response, filtered_app, environ)

    def test_start_response_called_twice(self):
        def broken_app(environ, start_response):
            start_response("200 Okay", [])
            start_response("200 Okay", [])
            return iter([])     # pragma: no cover
        filtered_app = self.make_filter(broken_app)
        environ = {'X_REDIRECT_MAP': '/'}
        self.assertRaises(StartResponseCalledTwice,
                          get_response, filtered_app, environ)

class Test_filter_app_factory(unittest.TestCase):
    def call_it(self, app, global_config, **local_conf):
        from xsendfile_middleware import filter_app_factory
        return filter_app_factory(app, global_config, **local_conf)

    def test(self):
        def app(environ, start_response):
            start_response('200 Okay', [])
            return iter([])
        filtered_app = self.call_it(app, {})
        status, headers, app_iter = get_response(filtered_app)
        self.assertEqual(status, '200 Okay')

class Test_map_filename(unittest.TestCase):
    def call_it(self, filename, redirect_map):
        from xsendfile_middleware import _map_filename
        return _map_filename(filename, redirect_map)

    def test_relative_filename(self):
        filename = 'fn'
        redirect_map = os.getcwd() + '/=/mapped/'
        uri = self.call_it(filename, redirect_map)
        self.assertEqual(uri, '/mapped/fn')

    def test_non_mapped_prefix(self):
        filename = '/path/fn'
        redirect_map = '/path/'
        uri = self.call_it(filename, redirect_map)
        self.assertEqual(uri, '/path/fn')

    def test_multiple_mappings(self):
        filename = '/path2/fn'
        redirect_map = '/path1/=/mapped1/,/path2/=/mapped2/,/path3/=/mapped3/'
        uri = self.call_it(filename, redirect_map)
        self.assertEqual(uri, '/mapped2/fn')

    def test_no_matching_mapping(self):
        filename = '/path2/fn'
        redirect_map = '/path/=/mapped/'
        uri = self.call_it(filename, redirect_map)
        self.assertEqual(uri, None)

    def test_non_ascii_filename(self):
        filename = '/' + unichr(0xf8) + '/'
        redirect_map = filename + '=/o/'
        # Convert to PEP-3333 "string of bytes"
        redirect_map = redirect_map.encode('utf8').decode('latin1')
        uri = self.call_it(filename, redirect_map)
        self.assertEqual(uri, None)

# Ripped-off from pyramid
class TestFileIter(unittest.TestCase):
    def _makeOne(self, file, block_size):
        from xsendfile_middleware import FileWrapper
        return FileWrapper(file, block_size)

    def test___iter__(self):
        f = io.BytesIO(b'abc')
        inst = self._makeOne(f, 1)
        self.assertEqual(inst.__iter__(), inst)

    def test_iteration(self):
        data = b'abcdef'
        f = io.BytesIO(b'abcdef')
        inst = self._makeOne(f, 1)
        r = b''
        for x in inst:
            self.assertEqual(len(x), 1)
            r+=x
        self.assertEqual(r, data)

    def test_close(self):
        f = io.BytesIO(b'abc')
        inst = self._makeOne(f, 1)
        inst.close()
        self.assertTrue(f.closed)

def get_response(app, environ=None):
    if environ is None:
        environ = {}

    response = []
    output = []

    def start_response(status, response_headers, exc_info=None):
        if exc_info and not output:
            reraise(*exc_info)
        elif response:
            raise StartResponseCalledTwice()

        response[:] = status, response_headers

        def save(data):
            output.append(data)
        return save

    app_iter = app(environ, start_response)
    if not response:
        raise StartResponseNeverCalled()
    status, headers = response
    if output:
        app_iter = itertools.chain(output, app_iter)
    return status, headers, app_iter

class DummyFile(object):
    def __init__(self, name):
        self.name = text_type(name)

class DummyFileWrapper(object):
    def __init__(self, file, block_size):
        self.file = file
        self.block_size = block_size

class DummyException(Exception):
    pass

class StartResponseCalledTwice(AssertionError):
    pass

class StartResponseNeverCalled(AssertionError):
    pass


def reraise(typ, value, tb):    # pragma: no cover
    # python 2/3 compatibility
    if sys.version_info < (3, 0):
        exec("raise typ, value, tb")
    else:
        assert value.__traceback__ is tb
        raise value
