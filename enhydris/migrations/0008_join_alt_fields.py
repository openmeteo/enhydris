import re

from django.db import DataError, migrations

SEPARATOR = "\n\n---ALT---\n\n"


def join_alt_fields(apps, schema_editor):
    for model in apps.app_configs["enhydris"].get_models():
        alt_fields = [
            field for field in model._meta.get_fields() if field.name.endswith("_alt")
        ]
        if not alt_fields:
            continue
        for obj in model.objects.all():
            for alt_field in alt_fields:
                field = [
                    field
                    for field in model._meta.get_fields()
                    if field.name == alt_field.name[:-4]
                ][0]
                value = getattr(obj, field.name)
                value_alt = getattr(obj, alt_field.name)
                if (not value_alt) or (value == value_alt):
                    # The _alt field is empty or the same as the main field, do nothing
                    continue
                elif not value:
                    # The main field is empty, set it to the _alt field
                    setattr(obj, field.name, value_alt)
                else:
                    # Both are nonempty, join them
                    if type(field).__name__ == "CharField":
                        fmt = "{} [{}]"
                    elif type(field).__name__ == "TextField":
                        fmt = "{}" + SEPARATOR + "{}"
                    else:
                        raise Exception(
                            "Field {}.{} is neither a CharField nor a TextField".format(
                                model.__name__, field.name
                            )
                        )
                    setattr(obj, field.name, fmt.format(value, value_alt))

                # Set the alt field to empty. Then, if we come again to the same object
                # (e.g. when iterating in Gentity, and then again in Station), there
                # won't be chaos.
                setattr(obj, alt_field.name, "")

                try:
                    obj.save()
                except DataError as e:
                    raise DataError(
                        "Couldn't save object {} (id={}); perhaps {}='{}' is too long. "
                        "Original message: {}".format(
                            model.__name__,
                            obj.id,
                            field.name,
                            getattr(obj, field.name),
                            str(e),
                        )
                    )


def unjoin_alt_fields(apps, schema_editor):
    for model in apps.app_configs["enhydris"].get_models():
        alt_fields = [
            field for field in model._meta.get_fields() if field.name.endswith("_alt")
        ]
        if not alt_fields:
            continue
        for obj in model.objects.all():
            for alt_field in alt_fields:
                field = [
                    field
                    for field in model._meta.get_fields()
                    if field.name == alt_field.name[:-4]
                ][0]
                value = getattr(obj, field.name)
                if type(field).__name__ == "CharField":
                    if "[" not in value or value[-1] != "]":
                        continue
                    value, value_alt = re.match(
                        r"(.*?) \[(.*)\]$", value, flags=re.DOTALL
                    ).groups()
                elif type(field).__name__ == "TextField":
                    if SEPARATOR not in value:
                        continue
                    value, value_alt = value.split(SEPARATOR)
                else:
                    raise Exception(
                        "Field {}.{} is neither a CharField nor a TextField".format(
                            model.__name__, field.name
                        )
                    )
                setattr(obj, field.name, value)
                setattr(obj, alt_field.name, value_alt)
                obj.save()


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0007_make_station_coordinates_not_null")]

    operations = [migrations.RunPython(join_alt_fields, unjoin_alt_fields)]
