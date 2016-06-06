# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from enhydris.hcore.models import Timeseries

# When the data are moved from the tsrecords table to files in migration
# 0008_move_data_to_datafile, the new Timeseries model fields that hold the
# start and end date of the time series need to be updated. When I wrote
# migration 0008, I thought that "timeseries.save()" would do that; however,
# during migrations, Django doesn't call custom save() methods (and for a good
# reason), so this didn't work. This migration is added in order to make that
# update.
#
# Normally we shouldn't be importing directly from enhydris.hcore.models, as
# we've done above, because this gets the latest status of the model and not
# the historical. The correct way to do it would be to duplicate some of the
# date updating code into the migration. However, we violate this rule because
# it results in much simpler code, and because this migration is only used in
# the intermediate Enhydris version 0.7, after which migrations are redone from
# scratch; so the code of enhydris.hcore.models is going to change very little,
# if at all, for the rest of this branch.


def update_timeseries_start_and_end_date(apps, schema_editor):
    for timeseries in Timeseries.objects.all():
        timeseries.save()


class Migration(migrations.Migration):

    dependencies = [
        ('hcore', '0011_rename_start_end_date'),
    ]

    operations = [
        migrations.RunPython(update_timeseries_start_and_end_date),
    ]
