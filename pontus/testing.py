import unittest
from pyramid.config import Configurator
from pyramid.testing import DummyRequest
from pyramid import testing


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

    def tearDown(self):
        from dace.processinstance import event
        with event.callbacks_lock:
            for dc_or_stream in event.callbacks.values():
                if hasattr(dc_or_stream, 'close'):
                    dc_or_stream.close()
                else:
                    dc_or_stream.stop()

            event.callbacks = {}

        from dace.objectofcollaboration.system import CRAWLERS
        for crawler in CRAWLERS:
            crawler.stop()

        import shutil
        testing.tearDown()
        self.db.close()
        shutil.rmtree(self.tmpdir)
