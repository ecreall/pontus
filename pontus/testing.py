# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi

"""Functional test harness.

Same shape as dace's: a real Pyramid app (substanced + dace + pontus)
on a temporary file ZODB, request extensions applied, admin logged in.
Pontus's own suite and nova-ideo's functional layers build on it.
"""
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

    """Base class of the functional layers (see module docstring)."""
    def setUp(self):
        import tempfile
        import os.path
        self.tmpdir = tempfile.mkdtemp()
        dbpath = os.path.join( self.tmpdir, 'test.db')
        uri = 'file://' + dbpath
        settings = {'zodbconn.uri': uri,
                    # pyramid_tm annotates the transaction with the user
                    # *before* traversal; substanced 1.0b1's groupfinder
                    # then reads request.context, which does not exist
                    # yet. Hosts on the modern stack need this too (M4).
                    'tm.annotate_user': 'false',
                    'substanced.secret': 'sosecret',
                    'substanced.initial_login': 'admin',
                    'substanced.initial_password': 'admin',
                    'pyramid.includes': [
                        'substanced',
                        'pyramid_chameleon',
                        'pyramid_layout',
                        'pyramid_tm',
                        'dace',
                        'pontus',
        ]}

        app = main({}, **settings)
        # The historical 'pyramid_mailer.testing' include (placed after
        # substanced to override the mailer) now conflicts: substanced
        # >= 1.0b1 registers request.mailer itself. Same override, done
        # directly on the registry (Phase 3 / M2):
        from pyramid_mailer.testing import DummyMailer
        from pyramid_mailer.interfaces import IMailer
        app.registry.registerUtility(DummyMailer(), IMailer)
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
