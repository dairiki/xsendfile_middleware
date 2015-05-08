from setuptools import setup, find_packages
import os

version = '0.1a3'

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

setup(name='xsendfile_middleware',
      version=version,
      description="WSGI middleware to send files using X-Accel-Redirect",
      long_description=README + "\n\n" + CHANGES,
      platforms = ['Any'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Paste',
          'Framework :: Pyramid',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
          ],
      keywords='wsgi middleware paste x-accel-redirect nginx file_wrapper',
      author='Jeff Dairiki',
      author_email='dairiki@dairiki.org',
      url='https://github.com/dairiki/xsendfile_middleware',
      license='BSD',

      packages=find_packages(),
      zip_safe=True,

      entry_points={
          'paste.filter_app_factory': [
              'main = xsendfile_middleware:filter_app_factory',
              ],
          },

      test_suite='xsendfile_middleware.test',
      )
