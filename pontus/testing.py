# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

import unittest
from pyramid.config import Configurator
from pyramid.testing import DummyRequest
from pyramid import testing

from substanced.db import root_factory

from dace.subscribers import stop_ioloop


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings, root_factory=root_factory)
    return config.make_wsgi_app()


class FunctionalTests(unittest.TestCase):

    def setUp(self):
        import tempfile
        import os.path
        self.tmpdir = tempfile.mkdtemp()
        dbpath = os.path.join( self.tmpdir, 'test.db')
        uri = 'file://' + dbpath
        settings = {'zodbconn.uri': uri,
                    'substanced.secret': 'sosecret',
                    'substanced.initial_login': 'admin',
                    'substanced.initial_password': 'admin',
                    'pyramid.includes': [
                        'substanced',
                        'pyramid_chameleon',
                        'pyramid_layout',
                        'pyramid_mailer.testing', # have to be after substanced to override the mailer
                        'pyramid_tm',
                        'dace',
                        'pontus',
        ]}

        app = main({}, **settings)
        self.db = app.registry._zodb_databases['']
        request = DummyRequest()
        testing.setUp(registry=app.registry, request=request)
        self.app = root_factory(request)
        request.root = self.app
        from webtest import TestApp
        self.testapp = TestApp(app)
        self.request = request
        import time; time.sleep(2)

    def tearDown(self):
        stop_ioloop()
        import shutil
        testing.tearDown()
        self.db.close()
        shutil.rmtree(self.tmpdir)
