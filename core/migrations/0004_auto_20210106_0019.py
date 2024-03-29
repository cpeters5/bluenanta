# Generated by Django 3.0.9 on 2021-01-06 00:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20210106_0016'),
    ]

    operations = [
        migrations.AddField(
            model_name='subtribe',
            name='family',
            field=models.ForeignKey(db_column='family', default='', on_delete=django.db.models.deletion.DO_NOTHING, to='core.Family'),
        ),
        migrations.AddField(
            model_name='tribe',
            name='family',
            field=models.ForeignKey(db_column='family', default='', on_delete=django.db.models.deletion.DO_NOTHING, to='core.Family'),
        ),
    ]
