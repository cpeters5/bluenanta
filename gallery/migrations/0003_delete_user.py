# Generated by Django 3.2.15 on 2023-06-17 20:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0002_user'),
    ]

    operations = [
        migrations.DeleteModel(
            name='User',
        ),
    ]
