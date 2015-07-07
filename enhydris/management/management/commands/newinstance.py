from importlib import import_module
import os

from django.core.management.base import CommandError
from django.core.management.templates import TemplateCommand
from django.utils.crypto import get_random_string

import enhydris


class Command(TemplateCommand):
    help = ("Creates an Enhydris project directory structure for the given "
            "project name in the current directory or optionally in the given "
            "directory.")

    def add_arguments(self, parser):
        parser.add_argument('name',
                            help='Name of the application or project.')
        parser.add_argument('directory', nargs='?',
                            help='Optional destination directory')

    def handle(self, *args, **options):
        instance_name, target = options.pop('name'), options.pop('directory')
        self.validate_name(instance_name, 'project')

        # Check that the instance_name cannot be imported
        try:
            import_module(instance_name)
        except ImportError:
            pass
        else:
            raise CommandError("{} conflicts with the name of an existing "
                               "Python module and cannot be used as an "
                               "instance name. Please try another name."
                               .format(instance_name))

        # Create a random SECRET_KEY to put in the main settings
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        options['secret_key'] = get_random_string(50, chars)

        options['template'] = os.path.join(enhydris.__path__[0], 'conf')
        options['extensions'] = ['py']
        options['files'] = []
        options['enhydris_version'] = enhydris.__version__
        version_items = enhydris.__version__.split('.')
        if len(version_items) > 1:
            enhydris_docs_version = '{}.{}'.format(*version_items[:2])
        else:
            enhydris_docs_version = 'latest'
        options['enhydris_docs_version'] = enhydris_docs_version

        super(Command, self).handle('project', instance_name, target,
                                    **options)
