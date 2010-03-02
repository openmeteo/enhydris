import unittest

class SmokeTestCase(unittest.TestCase):
    """Test that all project URLs return correct status code."""
    #TODO: Run this for all applications, somehow
    #TODO: More customization: 404s, etc 
    #TODO: Make this run automatic for all 

    def setUp(self):
        self.pages = {
            200: [
                '/',
                '/stations/l/',
                '/accounts/login/',
                '/accounts/logout/',
                '/admin/',],
            404: [
                '/foob4r/',
                '/stations/foob4r/',
                '/stations/d/',
                '/account/foob4r/',]}

    def testStatusCode(self):
        """Test that the response status code is correct"""

        from django.test.client import Client
        client = Client()
        for expected_code, pages in self.pages.items():
            for page_url in pages:
                page = client.get(page_url)
                self.assertEquals(page.status_code, expected_code,
                    "Status code for page '%s' was %s instead of %s" %
                    (page_url, page.status_code, expected_code))

