# Generated by Django 3.2.15 on 2022-10-25 01:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0025_auto_20221025_0104'),
    ]

    operations = [
        migrations.AddField(
            model_name='distribution',
            name='dist',
            field=models.ForeignKey(db_column='dist', default=1, on_delete=django.db.models.deletion.CASCADE, to='other.location'),
            preserve_default=False,
        ),
    ]
