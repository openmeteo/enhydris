from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("enhydris", "0003_user_name")]

    operations = [migrations.DeleteModel(name="UserProfile")]
