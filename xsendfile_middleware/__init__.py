# -*- coding: utf-8 -*-
""" Middleware to set return x-accel-redirects for file responses.

This can be used to get nginx to send static files itself.

"""
from __future__ import absolute_import

import logging
import os

log = logging.getLogger(__name__)

def filter_app_factory(app, global_config, **local_conf):
    return xsendfile_middleware(app)

def xsendfile_middleware(application):
    def middleware(environ, start_response):
        redirect_map = environ.get('X_REDIRECT_MAP')
        if redirect_map:
            try:
                redirect_map = _ascii_str(redirect_map)
            except NotASCIIError:
                log.info("Ignoring non-ASCII value %r for X_REDIRECT_MAP",
                         redirect_map)
                redirect_map = None
        if not redirect_map:
            return application(environ, start_response)

        orig_file_wrapper = environ.get('wsgi.file_wrapper')
        environ['wsgi.file_wrapper'] = FileWrapper

        response = []
        writer = []

        def capture_response(status, response_headers, exc_info=None):
            if writer or response or exc_info:
                if response and not writer:
                    # We've been called once already, pass that call on up.
                    start_response(*response)
                writer[:] = [start_response(status, response_headers, exc_info)]
                return writer[0]        # pragma: NO COVER

            def deferred_write(data):
                if not writer:
                    writer.append(start_response(*response))
                return writer[0](data)

            response[:] = status, response_headers
            return deferred_write

        result = application(environ, capture_response)

        if writer:
            # upstream start_response already called
            return result
        elif not response:
            # Our start_response was never called. Oh well, pass the
            # problem on up.
            return result

        status, response_headers = response

        if isinstance(result, FileWrapper):
            redirect_uri = None
            name = getattr(result.file, 'name', None)
            if name:
                redirect_uri = _map_filename(name, redirect_map)
            if redirect_uri:
                # Note: Returned status seems to be ignored by nginx if
                # X-Accel-Redirect is set
                log.debug("X-Accel-Redirect to %r for %r", redirect_uri, name)
                remove_headers = ['content-length', 'x-accel-redirect']
                response_headers = [(header, value)
                                    for header, value in response_headers
                                    if header.lower() not in remove_headers]
                response_headers.append(('X-Accel-Redirect', redirect_uri))
                result = iter(())
            elif orig_file_wrapper:
                result = orig_file_wrapper(result.file, result.block_size)

        start_response(status, response_headers)
        return result

    return middleware

class NotASCIIError(Exception):
    pass

def _ascii_str(s):
    # According to PEP-3333, all "strings" used in the WSGI protocol
    # must be of type ``str``, yet they must really be a string of bytes.
    # This function converts strings to just such ``str``\s.
    #
    # As an added bit of paranoia, it ensures that the strings contain
    # nothing but ASCII characters.  (This restriction could probably
    # be relaxed, but, ATM, I'm not quite sure what encoding is
    # appropriate.)
    try:
        s = s.encode('ascii')
    except UnicodeEncodeError:
        raise NotASCIIError("%r is not an ASCII string", s)
    if not isinstance(s, str):
        # py3k
        return s.decode('latin1')  # pragma: no cover
    return s

def _map_filename(filename, redirect_map):
    filename = os.path.abspath(filename)
    try:
        filename = _ascii_str(filename)
    except NotASCIIError:
        log.info("Not mapping file with non-ASCII name %r", filename)
        return None

    for mapping in redirect_map.split(','):
        prefix, sep, base_uri = mapping.partition('=')
        if filename.startswith(prefix):
            if not sep:
                base_uri = prefix
            return base_uri + filename[len(prefix):]


_BLOCK_SIZE = 4096 * 64 # 256K

class FileWrapper(object):
    """ A fixed-block-size iterator for use as a WSGI app_iter.

    Ripped-off from pyramid.response.FileIter.

    ``file`` is a Python file pointer (or at least an object with a ``read``
    method that takes a size hint).

    ``block_size`` is an optional block size for iteration.
    """
    def __init__(self, file, block_size=_BLOCK_SIZE):
        self.file = file
        self.block_size = block_size

    def __iter__(self):
        return self

    def next(self):
        val = self.file.read(self.block_size)
        if not val:
            raise StopIteration
        return val

    __next__ = next # py3

    def close(self):
        self.file.close()
