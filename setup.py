import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.md')).read()

requires = [
    'ecreall_dace',
    'pyramid_layout',
    'substanced',
    'pillow'
    ]

setup(name='ecreall_pontus',
      version='2.0.0.dev0',
      description='An application programming interface built upon the Pyramid web framework and substanced application. It provides libraries which make it easy to manage complex and imbricated views. For that purpose, Pontus introduces the concept of operations on views.',
      long_description=README + '\n\n' +  CHANGES,
      long_description_content_type='text/markdown',
      classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.12",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        ],
      author='Amen Souissi',
      author_email='amensouissi@ecreall.com',
      maintainer='Michaël Launay (Logikascium)',
      url='https://github.com/michaellaunay/pontus/',
      project_urls={
          'Source': 'https://github.com/michaellaunay/pontus',
          'Tracker': 'https://github.com/michaellaunay/pontus/issues',
          'Historical upstream': 'https://github.com/ecreall/pontus',
      },
      keywords='pyramid views forms deform substanced',
      license="AGPLv3+",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires + ['mock'],
      test_suite="pontus",
      message_extractors={
          'pontus': [
              ('**.py', 'python', None), # babel extractor supports plurals
              ('**.pt', 'chameleon', None),
          ],
      },
      extras_require = dict(
          # mock: substanced's venusian scan imports its own test modules
          # (see docs/en/worklog.md, 2026-07-13)
          test=['WebTest', 'mock'],
      ),
      entry_points="""\
      """,
      )

