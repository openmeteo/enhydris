from django.db import migrations


def is_image(gentity_file):
    filename = gentity_file.content.name.lower()
    return (
        filename.endswith(".jpg")
        or filename.endswith(".jpeg")
        or filename.endswith(".png")
        or filename.endswith(".gif")
    )


def move_files_to_images(apps, schema_editor):
    GentityImage = apps.get_model("enhydris", "GentityImage")
    GentityFile = apps.get_model("enhydris", "GentityFile")
    for gentity_file in GentityFile.objects.all():
        if is_image(gentity_file):
            GentityImage.objects.create(
                last_modified=gentity_file.last_modified,
                gentity=gentity_file.gentity,
                date=gentity_file.date,
                content=gentity_file.content,
                descr=gentity_file.descr,
                remarks=gentity_file.remarks,
                featured=False,
            )
            gentity_file.delete()


def move_images_to_files(apps, schema_editor):
    GentityImage = apps.get_model("enhydris", "GentityImage")
    GentityFile = apps.get_model("enhydris", "GentityFile")
    for gentity_image in GentityImage.objects.all():
        GentityFile.objects.create(
            last_modified=gentity_image.last_modified,
            gentity=gentity_image.gentity,
            date=gentity_image.date,
            content=gentity_image.content,
            descr=gentity_image.descr,
            remarks=gentity_image.remarks,
        )
        gentity_image.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("enhydris", "0107_gentity_images"),
    ]

    operations = [
        migrations.RunPython(move_files_to_images, move_images_to_files),
    ]
