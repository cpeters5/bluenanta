# Generated by Django 3.2.15 on 2024-05-12 12:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orchidaceae', '0012_auto_20240512_1207'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='synonym',
            name='species',
        ),
    ]
