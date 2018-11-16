from django.db import migrations


def copy_user_names(apps, schema_editor):
    # In the next migration we will delete model UserProfile, which is mostly useless.
    # Before doing that, let's copy any useful information to auth.User. This is user
    # names.
    UserProfile = apps.get_model("enhydris", "UserProfile")
    User = apps.get_model("auth", "User")

    for user_profile in UserProfile.objects.all():
        # Nothing to do if user_profile has no name
        if not user_profile.fname and not user_profile.lname:
            continue
        user = User.objects.get(id=user_profile.user_id)

        # If there are names both in user and user_profile and they're not the same,
        # that's an error.
        assert (not user.first_name) or (user.first_name == user_profile.fname)
        assert (not user.last_name) or (user.last_name == user_profile.lname)

        # Otherwise we copy the names from user_profile to user
        if user_profile.fname:
            user.first_name = user_profile.fname
        if user_profile.lname:
            user.last_name = user_profile.lname

        user.save()


def reverse_migration(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0002_initial_data")]

    operations = [migrations.RunPython(copy_user_names, reverse_migration)]
