# Generated by Django 3.2.15 on 2024-03-04 18:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orchidaceae', '0002_auto_20240304_1749'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='species',
            name='conservation_status',
        ),
    ]
