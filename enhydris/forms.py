from captcha.fields import CaptchaField
from registration.forms import RegistrationFormTermsOfService


class RegistrationForm(RegistrationFormTermsOfService):
    """
    Extension of the default registration form to include a captcha
    """

    captcha = CaptchaField()
