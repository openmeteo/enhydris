import re

from django.conf import settings


class Migrator:
    """Migrates the data of a lookup so that is parler-based.

    Migrator(apps, schema_editor, "MyLookup").migrate() performs the data migration of
    MyLookup. Run it after creating the MyLookupTranslations, but before removing
    MyLookup.descr. See the release notes for Enhydris 3.0 for details on how it works.
    """

    def __init__(self, apps, schema_editor, model_name):
        self.model = apps.get_model("enhydris", model_name)
        self.model_translation = apps.get_model("enhydris", model_name + "Translation")
        self._find_default_language_code()
        self._find_second_language_code()

    def migrate(self):
        for obj in self.model.objects.all():
            self._do_obj(obj)

    def reverse_migrate(self):
        for obj in self.model.objects.all():
            self._reverse_do_obj(obj)

    def _find_default_language_code(self):
        try:
            self.default_language_code = settings.PARLER_DEFAULT_LANGUAGE_CODE
            return
        except AttributeError:
            pass
        try:
            self.default_language_code = settings.LANGUAGE_CODE
            return
        except AttributeError:
            pass
        self.default_language_code = "en"

    def _find_second_language_code(self):
        try:
            site_id = settings.SITE_ID
            self.second_language_code = settings.PARLER_LANGUAGES[site_id][1]["code"]
        except (IndexError, AttributeError):
            self.second_language_code = None

    def _do_obj(self, obj):
        if self._contains_translation(obj):
            self._do_obj_with_translation(obj)
        else:
            self._do_obj_without_translation(obj)

    def _contains_translation(self, obj):
        return self.second_language_code is not None and (
            "[" in obj.descr and "]" in obj.descr
        )

    def _do_obj_with_translation(self, obj):
        m = re.match(r"(.*?)\s*\[([^[\]]*)\]\s*$", obj.descr)
        main = m.group(1)
        translation = m.group(2)
        self._create_translation(obj, self.default_language_code, main)
        self._create_translation(obj, self.second_language_code, translation)

    def _create_translation(self, obj, language_code, string):
        self.model_translation.objects.create(
            master_id=obj.pk, language_code=language_code, descr=string
        )

    def _do_obj_without_translation(self, obj):
        self._create_translation(obj, self.default_language_code, obj.descr)

    def _reverse_do_obj(self, obj):
        if self._has_second_language(obj):
            self._reverse_do_obj_with_translation(obj)
        else:
            self._reverse_do_obj_without_translation(obj)

    def _has_second_language(self, obj):
        return (
            self.second_language_code is not None
            and self.model_translation.objects.filter(
                master=obj, language_code=self.second_language_code
            ).exists()
        )

    def _reverse_do_obj_with_translation(self, obj):
        objs = self.model_translation.objects
        obj.descr = "{} [{}]".format(
            objs.get(master=obj, language_code=self.default_language_code).descr,
            objs.get(master=obj, language_code=self.second_language_code).descr,
        )
        obj.save()

    def _reverse_do_obj_without_translation(self, obj):
        obj.descr = self.model_translation.objects.get(
            master=obj, language_code=self.default_language_code
        ).descr
        obj.save()
