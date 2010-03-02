import sha
from os import remove
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext, Context
from django import forms
from django.forms.widgets import *
from django.core.mail import mail_managers, BadHeaderError
from django.template.loader import render_to_string
from enhydris.contact.forms import ContactForm

# global salt var
SALT = settings.SECRET_KEY[:5]
IMAGE_URL = settings.CAPTCHA_ROOT

def contactview(request):
    """
    This is the main view that renders the contact form and sends the email
    when the form is submitted.
    """
    subject = request.POST.get('subject', '')
    name = request.POST.get('name', '')
    message = request.POST.get('message', '')
    from_email = request.POST.get('email', '')

    # send the mail
    if subject and message and from_email:
        # copy data so we can manipulate them
        data = request.POST.copy()
        remove(IMAGE_URL+data['hash']+".jpg")

        # check captcha
        if data['hash'] == sha.new(SALT+data['captcha']).hexdigest():


            # format the email
            rendered_message = render_to_string('contact/email_body.txt',
                                                    {'user': name,
                                                     'email': from_email,
                                                     'message': message,})
            try:
                mail_managers(subject, rendered_message)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')

            return render_to_response('contact/thankyou.html',
                                        RequestContext(request))

        else:

            (captcha, hash) = createcapcha(request)
            return render_to_response('contact/contact.html',
                                    {'form': ContactForm(),
                                    'captcha': captcha, 'hash':hash,
                                    'message':'Wrong captcha'},
                                    RequestContext(request))


    hash = createcapcha(request)
    captcha_img = hash+'.jpg'

    return render_to_response('contact/contact.html', {'form': ContactForm(),
                                    'captcha': captcha_img, 'hash':hash},
                                    RequestContext(request))

def createcapcha(request):
    """
    This is a simple view which creates a captcha image and returns the name of
    the image to pass to the template.
    """
    from random import choice
    # PIL elements, sha for hash
    import Image, ImageDraw, ImageFont

    imgtext = ''.join([choice('QWERTYUOPASDFGHJKLZXCVBNM') for i in range(5)])
    imghash = sha.new(SALT+imgtext).hexdigest()
    im = Image.new("RGB", (90,20), (600,600,600))
    draw=ImageDraw.Draw(im)
    font=ImageFont.truetype(settings.CAPTCHA_FONT, 18)
    draw.text((3,0),imgtext, font=font, fill=(000,000,50))
    temp = IMAGE_URL + imghash + '.jpg'
    print temp
    im.save(temp, "JPEG")

    return imghash
