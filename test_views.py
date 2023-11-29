from django.test import TestCase
from django.core.management import call_command
from utils.testing import helpers
import json

class TestViews(TestCase):
    def setUp(self):
        self.press = helpers.create_press()
        self.press.domain = "testserver"
        self.press.save()
        self.user = helpers.create_user("a@b.edu")
        self.user.is_active = True
        self.user.is_staff = True
        self.user.save()
        self.journal1, self.journal2 = helpers.create_journals()
        # we have to call install for the views to be available
        call_command('install_plugins', 'journal_transporter')

    def test_no_authentication(self):
        response = self.client.get('/plugins/journal-transporter-plugin-for-janeway-14/journals/')
        self.assertEqual(response.status_code, 403)
        j = json.loads(response.content)
        self.assertEqual(j["detail"], "Authentication credentials were not provided.")

    def test_authentication(self):
        self.client.force_login(user=self.user)
        response = self.client.get('/plugins/journal-transporter-plugin-for-janeway-14/journals/')
        self.assertEqual(response.status_code, 200)
        j = json.loads(response.content)
        self.assertEqual(j["count"], 2)
        self.assertEqual(len(j["results"]), 2)