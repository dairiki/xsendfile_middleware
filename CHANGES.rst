=======
Changes
=======

0.1.1 (2016-10-28)
==================

(Release 0.1 does not exist.  It had corrupt rST in its PKG-INFO
causing the README on PyPI not to be formatted.)

No changes (other than test configuration) from 0.1a3.  This package
has been used in production for years now — might as well drop the
“alpha” designation.

Testing
-------

* Drop support for python 3.2.  Now tested under pythons 2.6, 2.7,
  3.3, 3.4, 3.5, pypy and pypy3.

0.1a3 (2015-05-08)
==================

Brown bag.  The previous release was unusable do to this bug:

* Make sure not to include unicode strings in the headers passed to
  ``start_response``.

0.1a2 (2015-05-08)
==================

* Py3k, pypy compatibility: the tests now run under python 2.6, 2.7,
  3.2, 3.3, 3.4, pypy and pypy3.

0.1a1 (2013-12-11)
==================

Initial Release
