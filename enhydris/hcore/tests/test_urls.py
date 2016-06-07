from django.test import TestCase
from django.test.utils import override_settings


class SmokeTestCase(TestCase):
    """Test that all project URLs return correct status code."""
    #TODO: Run this for all applications, somehow
    #TODO: More customization: 404s, etc
    #TODO: Make this run automatic for all

    pages = {
        200: ['/',
              '/accounts/login/',
              '/accounts/logout/',
              '/accounts/register/',
              '/accounts/password/reset/',
              '/accounts/password/reset/done/',
              ],
        301: ['/stations/l/',
              ],
        302: ['/admin/',  # This redirects to a login page
              ],
        404: ['/nonexistent/',
              '/stations/d/',
              '/stations/d/nonexistent/',
              '/timeseries/d/',
              '/timeseries/d/nonexistent/',
              '/instruments/d/',
              '/instruments/d/nonexistent/',
              '/account/foob4r/',
              ],
    }

    @override_settings(REGISTRATION_OPEN=True)
    def testStatusCode(self):
        """Test that the response status code is correct"""

        for expected_code in self.pages:
            for page_url in self.pages[expected_code]:
                page = self.client.get(page_url)
                self.assertEqual(
                    page.status_code, expected_code,
                    "Status code for page '%s' was %s instead of %s" %
                    (page_url, page.status_code, expected_code))
