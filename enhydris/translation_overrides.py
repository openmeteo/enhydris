"""Overriding of translations in third-party apps.

Sometimes we need to override translation messages in third-party apps. If we just add
the messages in django.po, they will be commented out the next time we run makemessages.
So we put these messages in here. See also https://stackoverflow.com/a/20439571/662345
"""

from django.utils.translation import gettext as _

messages_to_override = [
    # For this message, see enhydris.api.tests.test_views.test_misc.GetTokenTestCase
    _('Method "{method}" not allowed.'),
]
