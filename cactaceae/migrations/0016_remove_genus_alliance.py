# Generated by Django 3.1 on 2021-04-25 21:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cactaceae', '0015_remove_genus_binomial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='genus',
            name='alliance',
        ),
    ]
