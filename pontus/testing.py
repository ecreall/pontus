import unittest
from pyramid.config import Configurator
from pyramid.testing import DummyRequest
from pyramid import testing
from dace.objectofcollaboration.object import Object


from substanced.db import root_factory


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
            'pyramid_chameleon',
            'pyramid_layout',
            'pyramid_mailer.testing',
            'pyramid_tm',
            'substanced',
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

    def tearDown(self):
        import shutil
        testing.tearDown()
        self.db.close()
        shutil.rmtree(self.tmpdir)
