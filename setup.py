import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [
    'ecreall_dace',
    'pyramid_layout',
    'substanced',
    'pillow'
    ]

setup(name='ecreall_pontus',
      version='1.0.1',
      description='An application programming interface built upon the Pyramid web framework and substanced application. It provides libraries which make it easy to manage complex and imbricated views. For that purpose, Pontus introduces the concept of operations on views.',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        ],
      author='Amen Souissi',
      author_email='amensouissi@ecreall.com',
      url='https://github.com/ecreall/pontus/',
      keywords='process',
      license="AGPLv3+",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="pontus",
      message_extractors={
          'pontus': [
              ('**.py', 'python', None), # babel extractor supports plurals
              ('**.pt', 'chameleon', None),
          ],
      },
      extras_require = dict(
          test=['WebTest'],
      ),
      entry_points="""\
      """,
      )

