# Generated by Django 3.2.5 on 2022-01-06 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_auto_20211109_1221'),
    ]

    operations = [
        migrations.AddField(
            model_name='family',
            name='orig_pid',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
