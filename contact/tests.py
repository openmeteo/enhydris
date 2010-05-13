import sha
import unittest
from django.conf import settings
from django.test.client import Client

class SmokeTestCase(unittest.TestCase):
    """Test for contact app."""

    def setUp(self):
        self.client = Client()
        self.pages = {
            200: [
                '/contact/'
                ],
            404: [
                '/contact/foo/'
                ]}

    def testStatusCode(self):
        """Test that the response status code is correct"""

        for expected_code, pages in self.pages.items():
            for page_url in pages:
                page = self.client.get(page_url)
                self.assertEquals(page.status_code, expected_code,
                    "Status code for page '%s' was %s instead of %s" %
                    (page_url, page.status_code, expected_code))

    def testCaptcha(self):
        """Test captcha is working"""

        SALT = settings.SECRET_KEY[:5]

        post_data = {
            'email':'test@test.com',
            'name':'Tester',
            'subject':'test mail',
            'message':'test message',
            'captcha':'asdf',
            'hash': sha.new(SALT+'asdf').hexdigest()
        }

        response = self.client.post('/contact/', post_data)
        self.assertEqual(response.status_code, 200)
