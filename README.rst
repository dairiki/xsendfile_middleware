==========================================================
WSGI Middleware to Support X-Accel-Redirect |build status|
==========================================================

Description
===========

Nginx_ has a mechanism whereby, by returning an `X-Accel-Redirect`_ header,
a web app may convince nginx to serve a static file directly.
`PEP 333`_ defines a mechanism whereby an app server (or middleware)
can offer to serve files directly by providing ``wsgi.file_wrapper``
in the ``environ``.
This package provides a piece of WSGI middleware to take advantage of those
two mechanisms.

Despite the name of the package, currently this middleware only works
with nginx’s ``X-Accel-Redirect`` mechanism. (It would probably be
straightforward to generalize it so that it works ``X-Sendfile``, but
at the moment, I have no need for that.)

.. _Nginx: http://nginx.org/en/
.. _X-Accel-Redirect: http://wiki.nginx.org/X-accel
.. _PEP 333: http://www.python.org/dev/peps/pep-0333/
.. _wsgi.file_wrapper:
     http://www.python.org/dev/peps/pep-0333/#optional-platform-specific-file-handling


Download & Source
=================

The source repository is on github__.
You may submit bug reports and pull requests there.

__ https://github.com/dairiki/xsendfile_middleware/

It is also available via PyPI__.

__ https://pypi.python.org/pypi/xsendfile_middleware/


Usage
=====

The middleware is ``xsendfile_middleware.xsendfile_middleware``.
You can call it directly, e.g.::

    from xsendfile_middleware import xsendfile_middleware

    def main(**settings):
        """ Construct and return a filtered app.
        """
        def my_app(environ, start_response):
            # ...
            return app_iter

        # wrap middleware around app
        return xsendfile_middleware(my_app)

There is also a suitable entry point provided so that you can instantiate
the middleware from a PasteDeploy_ ``.ini`` file, e.g.::

    [app:myapp]
    use = egg:MyEgg

    [pipeline:main]
    pipeline = egg:xsendfile_middleware myapp

.. _PasteDeploy: http://pythonpaste.org/deploy/

Configuration
=============

X_REDIRECT_MAP
--------------

Once you have the middleware in place, the only configuration needed
(or possible) is to set an ``X_REDIRECT_MAP`` key in the WSGI environ.
How you do that depends on how you’ve got things set up.  If you are
running your app under uwsgi_, for example, then you can use something
like the following in your ``nginx`` config::

  location /app {
    uwsgi_pass 127.0.0.1:6543;
    include uwsgi_params;

    uwsgi_param X_REDIRECT_MAP /path/to/files/=/_redir_/;
  }

  location /_redir_/ {
    internal;
    alias /path/to/files/;
  }

In this configuration, if your app returns an app_iter which is
an instance of the file wrapper provided by the middleware, and
that wrapper wraps file at, *e.g.*,
``/path/to/files/dir/file.data``,
the middleware will set an ``X-Accel-Redirect: /_redir_/dir/file.data``
header in the response.  (This, hopefully, will cause nginx to send
the desired file directly to the client.)

.. _uwsgi: http://uwsgi-docs.readthedocs.org/en/latest/

The format of ``X_REDIRECT_MAP`` is a comma-separated list of
“``/prefix/=/base_uri/``” mappings.  As a short-cut, “``/prefix/``”
(with no equals sign) means the same as “``/prefix/=/prefix/``” (an
``X-Accel-Redirect`` header containing the original file name will be
sent for matching paths.)  The entries in the map are checked in
order; the first matching entry wins.  If none of the entries match,
then the middleware will pass the response on up the chain unmolested.

**Warning**:
The parsing of ``X_REDIRECT_MAP`` is rather simplistic.  Things will
probably not go well if you try to include commas, equal signs,
or any non-ASCII characters in either the *prefix* or *base_uri*.
Also, do not include any extraneous white space in ``X_REDIRECT_MAP``.

Author
======

This package was written by `Jeff Dairiki`_.

.. _Jeff Dairiki: mailto:dairiki@dairiki.org

.. |build status| image::
    https://travis-ci.org/dairiki/xsendfile_middleware.svg?branch=master
    :target: https://travis-ci.org/dairiki/xsendfile_middleware
