# Generated by Django 3.2.15 on 2022-10-24 22:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('other', '0016_auto_20221024_2200'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='distlocation',
            unique_together={('pid', 'dist')},
        ),
    ]
