import unittest

from webtest import TestApp

from google.appengine.api import users
from google.appengine.ext import testbed
from google.appengine.ext import webapp
import main

class ManageHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_user_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def loginUser(self, email='test@example.com', id='Rui', is_admin=True):
        self.testbed.setup_env(
            user_email=email,
            user_id=id,
            user_is_admin='1' if is_admin else '0',
            overwrite=True)

    def testLogin(self):
        app = TestApp(main.app)
        self.assertFalse(users.get_current_user())
        self.loginUser()
        resp = app.get('/manage')
        print(resp.status)