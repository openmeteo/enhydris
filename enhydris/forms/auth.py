from django.utils.translation import ugettext_lazy as _

from captcha.fields import CaptchaField
from registration.forms import RegistrationFormTermsOfService


class MyRegistrationForm(RegistrationFormTermsOfService):
    captcha = CaptchaField(label=_("Are you human?"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = _(
            "150 characters or fewer. Letters, digits and @/./+/-/_ only."
        )
