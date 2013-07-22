.. _contact:

:mod:`contact` --- Enhydris Contact App
=======================================

.. module:: contact
   :synopsis: Enhydris Contact Form
.. moduleauthor:: Seraphim Mellos <mellos@indifex.com>
.. sectionauthor:: Seraphim Mellos <mellos@indifex.com>

The `contact` application implements a single view which presents to the user
a contact form and by using it the user can contact the website
administrators. By default, all user emails are sent to all the administrators
as specified by the ``ADMINS`` tupple in ``settings.py``.

.. note::

	The ``contact`` application for each request of the contact page, creates
	a new captcha image and saves it in the CAPTCHA_DIR, which is defined in
	the ``settings.py`` file. Since the captcha images don't get removed from
	the disk until someone succesfully submits a message with the specified
	captcha, over long time periods the captcha folder may get filled up with
	images and will probably require a periodic cleanup. A nice way to handle
	this would be to create a weekly cronjob which clears the whole captcha
	directory.
