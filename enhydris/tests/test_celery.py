from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings

from ..celery import email_failed_task


class Sender:
    pass


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@override_settings(ADMINS=[("Alice", "alice@example.com")])
class EmailFailedTaskTestCase(TestCase):
    def _email_failed_task(self):
        sender = Sender()
        sender.name = "Alice"
        email_failed_task(
            sender=sender,
            exception=Exception("Things went wrong\n"),
            task_id="42",
            einfo="Things went really wrong",
        )

    @override_settings(ENHYDRIS_CELERY_SEND_TASK_ERROR_EMAILS=False)
    def test_nosend(self):
        self._email_failed_task()
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(ENHYDRIS_CELERY_SEND_TASK_ERROR_EMAILS=True)
    def test_send(self):
        self._email_failed_task()
        self.assertEqual(len(mail.outbox), 1)
